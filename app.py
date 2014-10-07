# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Flame app to send things to review.
"""

import os
import sys
import uuid
import platform


from sgtk.platform import Application


class FlameReview(Application):
    """
    Export functionality to automate and streamline content export out of Flame.
    """
    
    def init_app(self):
        """
        Called as the application is being initialized.
        """
        self.log_debug("%s: Initializing" % self)

        # keep track of the shotgun sequence that items are associated with
        self._sequence = None
        
        # register our desired interaction with flame hooks
        menu_caption = self.get_setting("menu_name")
        
        # set up callbacks for the engine to trigger 
        # when this profile is being triggered 
        callbacks = {}
        callbacks["preCustomExport"] = self.pre_custom_export
        callbacks["preExportAsset"] = self.adjust_path
        callbacks["postExportAsset"] = self.register_post_asset_job
        
        # register with the engine
        self.engine.register_export_hook(menu_caption, callbacks)
        


    def pre_custom_export(self, session_id, info):
        """
        Hook called before a custom export begins. The export will be blocked
        until this function returns. This can be used to fill information that would
        have normally been extracted from the export window.
        
        :param info: Dictionary with info about the export. Contains the keys
                     - destinationHost: Host name where the exported files will be written to.
                     - destinationPath: Export path root.
                     - presetPath: Path to the preset used for the export.
                     - abort: Pass True back to flame if you want to abort
                     - abortMessage: Abort message to feed back to client
        """
        # populate the host to use for the export. Currently hard coded to local
        info["destinationHost"] = "localhost"
        # set the (temp) location where media is being output prior to upload.
        info["destinationPath"] = self.execute_hook_method("settings_hook", "get_target_location")
        # pick up the xml export profile from the configuration
        info["presetPath"] = self.execute_hook_method("settings_hook", "get_export_preset")

        self.log_debug("%s: Starting custom export session with preset '%s'" % (self, info["presetPath"]))


                
    def adjust_path(self, session_id, info):
        """
        Called when an item is about to be exported and a path needs to be computed
 
        :param session_id: String which identifies which export session is being referred to
        :param info: metadata dictionary for the publish        
        """
        if info.get("assetType") != "video":
            # the review system ignores any other assets
            return
        
        # ensure each quicktime gets a unique name
        info["resolvedPath"] = "shotgun_%s.mov" % uuid.uuid4().hex
         
        
    def register_post_asset_job(self, session_id, info):
        """
        Called when an item has been exported.
        
        :param session_id: String which identifies which export session is being referred to
        :param info: metadata dictionary for the publish
        """
        
        if info.get("assetType") != "video":
            return

        if info.get("isBackground"):
            run_after_job_id = info.get("backgroundJobId")
        else:
            run_after_job_id = None
        
        args = {"info": info}
        
        self.engine.create_local_backburner_job("Uploading quicktime to Shotgun", 
                                                "bla bla bla", 
                                                run_after_job_id,
                                                self, 
                                                "upload_to_shotgun",
                                                args)
        
        
    def upload_to_shotgun(self, info):
        
        sequence_name = info["sequenceName"]
        
        # first, ensure that the sequence exists in Shotgun
        sg_sequence_data = self.shotgun.find_one("Sequence", [["code", "is", sequence_name],
                                                              ["project", "is", self.context.project]]) 
        
        if not sg_sequence_data:
            
            # Create a new sequence in Shotgun
            # First see if we should assign a task template
            sequence_task_template_name = self.get_setting("sequence_task_template")
            sequence_template = None
            if sequence_task_template_name: 
                sequence_template = sg.find_one("TaskTemplate", [["code", "is", sequence_task_template_name]])
                if not sequence_template:
                    raise TankError("The task template '%s' specified in the sequence_task_template setting "
                                    "does not exist!" % sequence_task_template_name)
                
            sg_sequence_data = self.shotgun.create("Sequence", {"code": sequence_name, 
                                                    "description": "Created by the Shotgun Toolkit Flame integration.",
                                                    "task_template": sequence_template,
                                                    "project": self.context.project})

        # create version
        full_path = os.path.join( info["destinationPath"], info["resolvedPath"])
        
        data = {}
        data["code"] = "test"
        data["project"] = self.context.project
        data["entity"] = sg_sequence_data
        sg_version_data = self.shotgun.create("Version", data)
        
        self.log_debug("Uploading quicktime to shotgun version %s" % sg_version_data)
        self.shotgun.upload("Version", sg_version_data["id"], full_path, "sg_uploaded_movie")
        
        
        

        
        
        
