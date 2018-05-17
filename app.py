# Copyright (c) 2014 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Flame app to send sequences to review.
"""

import os
import uuid

from sgtk import TankError
from sgtk.platform import Application


class FlameReview(Application):
    """
    Review functionality to automate and streamline sequence review out of Flame.
    
    Generates quicktimes for the selected Flame sequences and uploads these to Shotgun.
    """

    def init_app(self):
        """
        Called as the application is being initialized.
        """
        self.log_debug("%s: Initializing" % self)

        # register our desired interaction with Flame hooks
        menu_caption = self.get_setting("menu_name")

        # track the comments entered by the user
        self._review_comments = ""

        # flag to indicate that something was actually submitted
        self._submission_done = False

        # set up callbacks for the engine to trigger 
        # when this profile is being triggered 
        callbacks = {}
        callbacks["preCustomExport"] = self.pre_custom_export
        callbacks["preExportAsset"] = self.adjust_path
        callbacks["postExportAsset"] = self.populate_shotgun
        callbacks["postCustomExport"] = self.display_summary

        # register with the engine
        self.engine.register_export_hook(menu_caption, callbacks)

    def pre_custom_export(self, session_id, info):
        """
        Flame hook called before a custom export begins. The export will be blocked
        until this function returns. This can be used to fill information that would
        have normally been extracted from the export window.
        
        :param session_id: String which identifies which export session is being referred to.
                           This parameter makes it possible to distinguish between different 
                           export sessions running if this is needed (typically only needed for
                           expert use cases).
                           
        :param info: Dictionary with info about the export. Contains the keys
                     - destinationHost: Host name where the exported files will be written to.
                     - destinationPath: Export path root.
                     - presetPath: Path to the preset used for the export.
                     - abort: Pass True back to Flame if you want to abort
                     - abortMessage: Abort message to feed back to client
        """
        from sgtk.platform.qt import QtGui

        # clear our flags
        self._submission_done = False

        # pop up a UI asking the user for description
        tk_flame_review = self.import_module("tk_flame_review")
        (return_code, widget) = self.engine.show_modal("Submit for Review", self, tk_flame_review.SubmitDialog)

        if return_code == QtGui.QDialog.Rejected:
            # user pressed cancel
            info["abort"] = True
            info["abortMessage"] = "User cancelled the operation."

        else:
            # get comments from user
            self._review_comments = widget.get_comments()

            # populate the host to use for the export. Currently hard coded to local
            info["destinationHost"] = self.engine.get_server_hostname()
            # set the (temp) location where media is being output prior to upload.
            info["destinationPath"] = self.engine.get_backburner_tmp()
            # pick up the xml export profile from the configuration
            info["presetPath"] = self.execute_hook_method("settings_hook", "get_export_preset")

            self.log_debug("%s: Starting custom export session with preset '%s'" % (self, info["presetPath"]))

        # Log usage metrics
        try:
            self.log_metric("Sequence Export", log_version=True)
        except:
            # ingore any errors. ex: metrics logging not supported
            pass

    def adjust_path(self, session_id, info):
        """
        Flame hook called when an item is about to be exported and a path needs to be computed.
 
        :param session_id: String which identifies which export session is being referred to.
                           This parameter makes it possible to distinguish between different 
                           export sessions running if this is needed (typically only needed for
                           expert use cases).

        :param info: Dictionary with a number of parameters:
        
           destinationHost: Host name where the exported files will be written to.
           destinationPath: Export path root.
           namePattern:     List of optional naming tokens.
           resolvedPath:    Full file pattern that will be exported with all the tokens resolved.
           name:            Name of the exported asset.
           sequenceName:    Name of the sequence the asset is part of.
           shotName:        Name of the shot the asset is part of.
           assetType:       Type of exported asset. ( 'video', 'movie', 'audio', 'batch', 'openClip', 'batchOpenClip' )
           width:           Frame width of the exported asset.
           height:          Frame height of the exported asset.
           aspectRatio:     Frame aspect ratio of the exported asset.
           depth:           Frame depth of the exported asset. ( '8-bits', '10-bits', '12-bits', '16 fp' )
           scanFormat:      Scan format of the exported asset. ( 'FIELD_1', 'FIELD_2', 'PROGRESSIVE' )
           fps:             Frame rate of exported asset.
           sequenceFps:     Frame rate of the sequence the asset is part of.
           sourceIn:        Source in point in frame and asset frame rate.
           sourceOut:       Source out point in frame and asset frame rate.
           recordIn:        Record in point in frame and sequence frame rate.
           recordOut:       Record out point in frame and sequence frame rate.
           track:           ID of the sequence's track that contains the asset.
           trackName:       Name of the sequence's track that contains the asset.
           segmentIndex:    Asset index (1 based) in the track.
           versionName:     Current version name of export (Empty if unversioned).
           versionNumber:   Current version number of export (0 if unversioned).        
        """
        if info.get("assetType") not in ["video", "movie"]:
            # the review system ignores any other assets. The export profiles are defined
            # in the app's settings hook, so technically there shouldn't be any other items
            # generated - but just in case there are (because of customizations), we'll simply
            # ignore these.
            return

        name = info.get("assetName", info.get("name"))  # ensure backward compatibility

        # ensure each quicktime gets a unique name
        info["resolvedPath"] = "%s.%s.mov" % (name, uuid.uuid4().hex)

        # If client override DL_PYTHON_HOOK_PATH env var, it changes the order python hook
        # are triggered and can change the value of the global hook useBackburnerPostExportAsset.
        # "useBackburner" bypass the global option and set the option for that specific export job.
        # use Flame to run the post-export callbacks (not backburner)
        info["useBackburner"] = False

    def populate_shotgun(self, session_id, info):
        """
        Flame hook called when an item has been exported.
        
        :param session_id: String which identifies which export session is being referred to.
                           This parameter makes it possible to distinguish between different 
                           export sessions running if this is needed (typically only needed for
                           expert use cases).

        :param info: Dictionary with a number of parameters:
        
           destinationHost: Host name where the exported files will be written to.
           destinationPath: Export path root.
           namePattern:     List of optional naming tokens.
           resolvedPath:    Full file pattern that will be exported with all the tokens resolved.
           name:            Name of the exported asset.
           sequenceName:    Name of the sequence the asset is part of.
           shotName:        Name of the shot the asset is part of.
           assetType:       Type of exported asset. ( 'video', 'movie', 'audio', 'batch', 'openClip', 'batchOpenClip' )
           isBackground:    True if the export of the asset happened in the background.
           backgroundJobId: Id of the background job given by the backburner manager upon submission. 
                            Empty if job is done in foreground.
           width:           Frame width of the exported asset.
           height:          Frame height of the exported asset.
           aspectRatio:     Frame aspect ratio of the exported asset.
           depth:           Frame depth of the exported asset. ( '8-bits', '10-bits', '12-bits', '16 fp' )
           scanFormat:      Scan format of the exported asset. ( 'FIELD_1', 'FIELD_2', 'PROGRESSIVE' )
           fps:             Frame rate of exported asset.
           sequenceFps:     Frame rate of the sequence the asset is part of.
           sourceIn:        Source in point in frame and asset frame rate.
           sourceOut:       Source out point in frame and asset frame rate.
           recordIn:        Record in point in frame and sequence frame rate.
           recordOut:       Record out point in frame and sequence frame rate.
           track:           ID of the sequence's track that contains the asset.
           trackName:       Name of the sequence's track that contains the asset.
           segmentIndex:    Asset index (1 based) in the track.       
           versionName:     Current version name of export (Empty if unversioned).
           versionNumber:   Current version number of export (0 if unversioned).

        """

        if info.get("assetType") not in ["video", "movie"]:
            # the review system ignores any other assets. The export profiles are defined
            # in the app's settings hook, so technically there shouldn't be any other items
            # generated - but just in case there are (because of customizations), we'll simply
            # ignore these.
            return

        # now typically quicktimes are generates as background jobs.
        # in that case, make sure our background job that we are submitting
        # to backburner gets executed *after* the quicktime generation has completed!
        if info.get("isBackground"):
            run_after_job_id = info.get("backgroundJobId")
        else:
            run_after_job_id = None

        # set up the arguments which we will pass (via backburner) to 
        # the target method which gets executed
        args = {"info": info, "comments": self._review_comments}

        # and populate UI params

        backburner_job_title = "%s %s - Shotgun Upload" % (self.get_setting("shotgun_entity_type"),
                                                           info.get("sequenceName"))
        backburner_job_desc = "Creates a new version record in Shotgun and uploads the associated Quicktime."

        # kick off async job
        self.engine.create_local_backburner_job(backburner_job_title,
                                                backburner_job_desc,
                                                run_after_job_id,
                                                self,
                                                "backburner_populate_shotgun",
                                                args,
                                                info.get("destinationHost"))

        # done!
        self._submission_done = True

    def backburner_populate_shotgun(self, info, comments):
        """
        This method is called via backburner and therefore runs in the background.
        It does all the heavy lifting in the app:
        - creates a Shotgun sequence (with task templates) if this doesn't exist
        - creates a version and links it up with the sequence
        - uploads the quicktime to the version
        
        :param info: Dictionary with a number of parameters:
        
           destinationHost: Host name where the exported files will be written to.
           destinationPath: Export path root.
           namePattern:     List of optional naming tokens.
           resolvedPath:    Full file pattern that will be exported with all the tokens resolved.
           name:            Name of the exported asset.
           sequenceName:    Name of the sequence the asset is part of.
           shotName:        Name of the shot the asset is part of.
           assetType:       Type of exported asset. ( 'video', 'movie', 'audio', 'batch', 'openClip', 'batchOpenClip' )
           isBackground:    True if the export of the asset happened in the background.
           backgroundJobId: Id of the background job given by the backburner manager upon submission. 
                            Empty if job is done in foreground.
           width:           Frame width of the exported asset.
           height:          Frame height of the exported asset.
           aspectRatio:     Frame aspect ratio of the exported asset.
           depth:           Frame depth of the exported asset. ( '8-bits', '10-bits', '12-bits', '16 fp' )
           scanFormat:      Scan format of the exported asset. ( 'FIELD_1', 'FIELD_2', 'PROGRESSIVE' )
           fps:             Frame rate of exported asset.
           sequenceFps:     Frame rate of the sequence the asset is part of.
           sourceIn:        Source in point in frame and asset frame rate.
           sourceOut:       Source out point in frame and asset frame rate.
           recordIn:        Record in point in frame and sequence frame rate.
           recordOut:       Record out point in frame and sequence frame rate.
           track:           ID of the sequence's track that contains the asset.
           trackName:       Name of the sequence's track that contains the asset.
           segmentIndex:    Asset index (1 based) in the track.       
           versionName:     Current version name of export (Empty if unversioned).
           versionNumber:   Current version number of export (0 if unversioned).

        :param comments: Review comments entered by the user.
         
        """

        full_path = os.path.join(info["destinationPath"], info["resolvedPath"])

        if not os.path.exists(full_path):
            raise TankError("Cannot find quicktime '%s'! Aborting upload." % full_path)

        self.log_debug("Begin Shotgun processing for %s..." % full_path)
        self.log_debug("File size is %s bytes." % os.path.getsize(full_path))

        # ensure that the entity exists in Shotgun
        entity_name = info["sequenceName"]
        entity_type = self.get_setting("shotgun_entity_type")

        sg_data = self.shotgun.find_one(entity_type, [["code", "is", entity_name],
                                                      ["project", "is", self.context.project]])

        if not sg_data:
            # Create a new item in Shotgun
            # First see if we should assign a task template
            # this is controlled via the app settings
            # if no task template is specified in the settings, 
            # the item will be created without tasks.
            self.log_debug("Creating a new item in Shotgun...")
            task_template_name = self.get_setting("task_template")
            task_template = None
            if task_template_name:
                task_template = self.shotgun.find_one("TaskTemplate", [["code", "is", task_template_name]])
                if not task_template:
                    raise TankError("The task template '%s' specified in the task_template setting "
                                    "does not exist!" % task_template_name)

            sg_data = self.shotgun.create(entity_type, {"code": entity_name,
                                                        "description": "Created by the Shotgun Flame integration.",
                                                        "task_template": task_template,
                                                        "project": self.context.project})

            self.log_debug("Created %s" % sg_data)

            # upload thumb
            self._upload_thumbnail(
                full_path,
                info["width"],
                info["height"],
                sg_data["type"],
                sg_data["id"]
            )

        # now start the version creation process
        self.log_debug("Will associate upload with Shotgun entity %s..." % sg_data)

        # create a version in Shotgun
        if info["versionNumber"] != 0:
            title = "%s v%03d" % (info["sequenceName"], info["versionNumber"])
        else:
            title = info["sequenceName"]

        data = {}
        data["code"] = title
        data["description"] = comments
        data["project"] = self.context.project
        data["entity"] = sg_data
        data["created_by"] = self.context.user
        data["user"] = self.context.user

        # general metadata for the version
        # for the frame range, there isn't very meaningful metadata we can add
        # and we don't have corresponding frames on disk
        # so set the first frame to 1 in order to normalize the frames from Flame
        # which typically start at 10:00:00.00
        #
        # also note that Flame is out-exclusive, meaning that if you have the 
        # frame range 100-111, it corresponds to the frames
        # 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110
        # 
        # We transform the above frame range (100-111) to be 1-10 in Shotgun with length 10. 
        #
        data["sg_first_frame"] = 1
        data["sg_last_frame"] = info["sourceOut"] - info["sourceIn"]
        data["frame_count"] = info["sourceOut"] - info["sourceIn"]
        data["frame_range"] = "%s-%s" % (data["sg_first_frame"], data["sg_last_frame"])
        data["sg_frames_have_slate"] = False
        data["sg_movie_has_slate"] = False
        data["sg_frames_aspect_ratio"] = info["aspectRatio"]
        data["sg_movie_aspect_ratio"] = info["aspectRatio"]

        # This is used to find the latest Version from the same department.
        # todo: make this configurable?
        data["sg_department"] = "Editorial"

        sg_version_data = self.shotgun.create("Version", data)

        self.log_debug("Created a version in Shotgun: %s" % sg_version_data)

        # upload quicktime to Shotgun
        if self.get_setting("bypass_shotgun_transcoding"):
            self.log_debug("Begin upload of explicit mp4 quicktime to Shotgun...")
            self.shotgun.upload(
                "Version",
                sg_version_data["id"],
                full_path,
                "sg_uploaded_movie_mp4"
            )
            self.log_debug("Upload complete!")

            # upload thumb
            self._upload_thumbnail(
                full_path,
                info["width"],
                info["height"],
                "Version",
                sg_version_data["id"]
            )

        else:
            self.log_debug("Begin upload of quicktime to Shotgun...")
            self.shotgun.upload("Version", sg_version_data["id"], full_path, "sg_uploaded_movie")
            self.log_debug("Upload complete!")

        # clean up
        try:
            self.log_debug("Trying to remove temporary quicktime file...")
            os.remove(full_path)
            self.log_debug("Temporary quicktime file successfully deleted.")
        except Exception, e:
            self.log_warning("Could not remove temporary file '%s': %s" % (full_path, e))

    def _upload_thumbnail(self, full_path, width, height, entity_type, entity_id):
        """
        Given a flame image sequence path, extract a thumbnail and upload
        to Shotgun for the given entity.

        :param full_path: flame path to render
        :param width: Width of image to extract
        :param height: Height of image to extract
        :param entity_type: Shotgun entity type to upload to
        :param entity_id: Shotgun id for reflection
        :return:
        """
        # now extract and upload a thumbnail
        # for the extraction, we use the readframe utility which is part of the wiretap library
        # Syntax:
        #
        # Usage: ./read_frame
        #   -n <clip node id> (if empty, generate 4x4 black media)
        #   [ -h <Wiretap server ID> (default = localhost) ]
        #   [ -W <display width> (default=same as source) ]
        #   [ -H <display height> (default=same as source) ]
        #   [ -b <output bits per pixel (24|32)> (default = 24) ]
        #   [ -i <zero-based start frame idx> (default = 0) ]
        #   [ -N <number of frames to output> (default = 1, -1 for all)
        #   [ -r (output raw RGB, default=jpg) ]
        #   [ -O (flip raw output orientation, default=bottom to top) ]
        #   [ -L (use lowest resolution available, default=highest) ]
        #   [ -c <compression factor [0,100]> (default = 100)
        #   [ -p <processing options> (default = none)
        #
        input_cmd = "%s -n \"%s@CLIP\" -h %s -W %s -H %s -L" % (self.engine.get_read_frame_path(),
                                                                full_path,
                                                                "%s:Gateway" % self.engine.get_server_hostname(),
                                                                width,
                                                                height)

        thumbnail_jpg = os.path.join(self.engine.get_backburner_tmp(), "tk_thumb_%s.jpg" % uuid.uuid4().hex)
        full_cmd = "%s > %s" % (input_cmd, thumbnail_jpg)
        self.log_debug("Executing %s" % full_cmd)
        if os.system(full_cmd) != 0:
            self.log_warning("Could not extract thumbnail! See error log for details.")
        else:
            try:
                self.log_debug("Wrote thumbnail %s" % thumbnail_jpg)
                self.sgtk.shotgun.upload_thumbnail(entity_type, entity_id, thumbnail_jpg)
                self.log_debug("Uploaded thumbnail to Shotgun.")
            finally:
                # clean up our temp file
                try:
                    os.remove(thumbnail_jpg)
                    self.log_debug("Removed temporary file '%s'." % thumbnail_jpg)
                except Exception, e:
                    self.log_warning("Could not remove temporary file '%s': %s" % (thumbnail_jpg, e))

    def display_summary(self, session_id, info):
        """
        Flame hook which is used to show summary UI to user
        
        :param session_id: String which identifies which export session is being referred to.
                           This parameter makes it possible to distinguish between different 
                           export sessions running if this is needed (typically only needed for
                           expert use cases).
        
        :param info: Information about the export. Contains the keys      
                     - destinationHost: Host name where the exported files will be written to.
                     - destinationPath: Export path root.
                     - presetPath: Path to the preset used for the export.
        
        """
        # pop up a UI asking the user for description
        tk_flame_review = self.import_module("tk_flame_review")
        self.engine.show_modal("Submission Summary", self, tk_flame_review.SummaryDialog, self._submission_done)
