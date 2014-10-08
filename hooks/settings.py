# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk import TankError
import os
import re

HookBaseClass = sgtk.get_hook_baseclass()

class ExportSettings(HookBaseClass):
    """
    This hook controls the settings that flame will use when it exports the quicktimes 
    prior to uploading them to Shotgun. It also lets a user control where on disk temporary
    quicktime files will be located.
    """

    def get_export_preset(self):
        """
        Return the path to a flame export preset that should be used when generating 
        a sequence quicktime.
        
        :returns: Path on disk to flame export preset 
        """
        return self._generate_profile_xml()

    def get_target_location(self):
        """
        Return the folder on disk where temporary quicktimes should be stored.
        These quicktimes will be automatically removed once they have been
        uploaded to shotgun.
        
        :returns: A directory on disk  
        """
        return "/tmp"


    ###############################################################################################
    # helper methods and internals
    
    def _write_content_to_file(self, content, file_name):
        """
        Helper method. Writes content to file and returns the path.
        The content will be written to the app specific cache location 
        on disk, organized by app instance name. The rationale is that 
        each app instance holds its own configuration, and the configuration
        generates one set of unique xml files.
        
        :param content: Data to write to the file
        :param file_name: The name of the file to create
        :returns: path to the created file
        """
        # determine location
        file_path = os.path.join(self.parent.cache_location, self.parent.instance_name, file_name)
        folder = os.path.dirname(file_path)

        # create folders
        if not os.path.exists(folder):
            old_umask = os.umask(0)
            os.makedirs(folder, 0777)
            os.umask(old_umask)
        
        # write data
        fh = open(file_path, "wt")
        fh.write(content)
        fh.close()
        
        self.parent.log_debug("Wrote temporary file '%s'" % file_path)
        return file_path
        
    def _generate_quicktime_settings(self):
        """
        Generate quicktime codec presets and return the path to 
        the generated file.
        
        :returns: path to quicktime codec presets (.cdxprof) xml file
        """ 

        xml = """<?xml version="1.0" encoding="UTF-8"?>
<codecprofile version="1.0">
   <format name="QuickTime">
      <essence name="video">
         <provider name="libquicktime">
            <codec name="H264E" longname="H264" type="video" description="Main Concept H264 Codec">
               <params presetName="High_1080i_6Mbits">
                  <param name="Target preset" internalname="target_preset" description="" type="enum" value="H264_HIGH" />
                  <param name="Frame-type options" internalname="frame_type" description="" type="section" />
                  <param name="GOP size" internalname="idr_interval" description="" type="int" min="1" max="300" value="33" />
                  <param name="B-Frames" internalname="numBframes" description="Number of B-frames between I and P" type="int" min="0" max="3" value="2" />
                  <param name="Adaptive B-frame decision" internalname="adaptive_b_frames" description="" type="bool" value="1" />
                  <param name="Automatic scene detection" internalname="vcsd_mode" description="" type="bool" value="1" />
                  <param name="Rate control" internalname="ratecontrol" description="" type="section" />
                  <param name="Rate control method" internalname="bit_rate_mode" description="" type="enum" value="Average bitrate" />
                  <param name="Bitrate" internalname="bit_rate" description="Bitrate in kbit/s. (Used in bitrate mode.)" type="int" min="1" max="1000000" value="6000" />
                  <param name="Max bitrate" internalname="max_bit_rate" description="Max bitrate in kbit/s. Must be greater than the bitrate. (Used in bitrate mode.)" type="int" min="1" max="1000000" value="8000" />
                  <param name="I-frame quantizer" internalname="quant_pI" description="Quantization value for I-frames. (Used in quantizer mode.)" type="int" min="1" max="51" value="24" />
                  <param name="P-frame quantizer" internalname="quant_pP" description="Quantization value for P-frames. (Used in quantizer mode.)" type="int" min="1" max="51" value="25" />
                  <param name="B-frame quantizer" internalname="quant_pB" description="Quantization value for B-frames. (Used in quantizer mode.)" type="int" min="1" max="51" value="27" />
                  <param name="Minimum quantizer" internalname="min_quant" description="Minimum quantization value. (Used in both mode.)" type="int" min="1" max="51" value="0" />
                  <param name="Maximum quantizer" internalname="max_quant" description="Maximum quantization value. (Used in both mode.)" type="int" min="1" max="51" value="51" />
                  <param name="Advanced" internalname="advanced" description="" type="section" />
                  <param name="Optimize rate-distortion cost" internalname="rd_optimization" description="" type="bool" value="1" />
               </params>
            </codec>
         </provider>
      </essence>
   </format>
</codecprofile>
        """
        
        path = self._write_content_to_file(xml, "quicktime_settings.cdxprof")
        return path
    
    def _generate_profile_xml(self):
        """
        Generate flame export profile settings suitable for generating a single quicktime 
        file to represent an entire sequence.
        
        :returns: path to export preset xml file
        """
        
        
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<preset version="4">
   <type>movie</type>
   <comment>Creates an 8-bit QuickTime file (H.264 1280x720 8Mbits).</comment>
   <movie>
      <fileType>QuickTime</fileType>
      <namePattern></namePattern>
      <yuvHeadroom>False</yuvHeadroom>
      <yuvColourSpace>PCS_UNKNOWN</yuvColourSpace>
      <operationalPattern>None</operationalPattern>
      <companyName>Autodesk</companyName>
      <productName>Smoke</productName>
      <versionName>2015.2.pr99</versionName>
   </movie>
   <video>
      <fileType>QuickTime</fileType>
      <codec>33622016</codec>
      <codecProfile>{CODE_PROFILE_PATH}</codecProfile>
      <namePattern></namePattern>
      <compressionQuality>50</compressionQuality>
      <transferCharacteristic>2</transferCharacteristic>
      <colorimetricSpecification>4</colorimetricSpecification>
      <publishLinked>False</publishLinked>
      <foregroundPublish>False</foregroundPublish>
      <overwriteWithVersions>False</overwriteWithVersions>
      <resize>
         <resizeType>fit</resizeType>
         <resizeFilter>lanczos</resizeFilter>
         <width>1280</width>
         <height>720</height>
         <bitsPerChannel>8</bitsPerChannel>
         <numChannels>3</numChannels>
         <floatingPoint>False</floatingPoint>
         <bigEndian>True</bigEndian>
         <pixelRatio>1</pixelRatio>
         <scanFormat>P</scanFormat>
      </resize>
   </video>
   <audio>
      <fileType>QuickTime</fileType>
      <codec>4026793986</codec>
      <codecProfile />
      <namePattern></namePattern>
      <mixdown>AsIs</mixdown>
      <sampleRate>48000</sampleRate>
      <bitRate>128</bitRate>
      <bitDepth>-1</bitDepth>
   </audio>
   <name>
      <framePadding>8</framePadding>
      <startFrame>0</startFrame>
      <useTimecode>False</useTimecode>
   </name>
</preset>
        """
        # first generate the quicktime presets and bind this up to the content above
        quicktime_settings_path = self._generate_quicktime_settings()
        # plug in the path to the quicktime preset
        resolved_xml = xml.replace("{CODE_PROFILE_PATH}", quicktime_settings_path)
        # write it to disk
        preset_path = self._write_content_to_file(resolved_xml, "export_preset.xml")
        
        return preset_path
        
