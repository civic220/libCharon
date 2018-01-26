# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

from typing import Optional
import xml.etree.ElementTree as ET #For writing XML manifest files.
import zipfile

from ..FileInterface import FileInterface #The interface we're implementing.
from ..OpenMode import OpenMode #To detect whether we want to read and/or write to the file.

##  A container file type that contains multiple 3D-printing related files that
#   belong together.
class UltimakerContainerFile(FileInterface):
    #Some constants related to this format.
    xml_header = ET.ProcessingInstruction("xml", "version=\"1.0\" encoding=\"UTF-8\"") #Header element being put atop every XML file.
    rels_file = "_rels/.rels" #Where the main relationships file is.
    content_types_file = "[Content_Types].xml" #Where the content types file is.

    def open(self, path: Optional[str] = None, mode: OpenMode = OpenMode.ReadOnly):
        self.mode = mode
        self.zipfile = zipfile.ZipFile(path, self.mode.value, compression = zipfile.ZIP_DEFLATED)

        #Load or create the content types element.
        self.content_types_element = None
        if self.content_types_file in self.zipfile.namelist():
            content_types_document = ET.fromstring(self.zipfile.open(self.content_types_file).read())
            content_types_element = content_types_document.find("Types")
            if content_types_element:
                self.content_types_element = content_types_element
        if not self.content_types_element:
            self.content_types_element = ET.Element("Types", xmlns = "http://schemas.openxmlformats.org/package/2006/content-types")
            if self.mode != OpenMode.ReadOnly:
                self._updateContentTypes()

        #Load or create the relations element.
        self.relations_element = None
        if self.rels_file in self.zipfile.namelist():
            relations_document = ET.fromstring(self.zipfile.open(self.rels_file).read())
            relations_element = relations_document.find("Relationships")
            if relations_element:
                self.relations_element = relations_element
        if not self.relations_element: #File didn't exist or didn't contain a Relationships element.
            self.relations_element = ET.Element("Relationships", xmlns = "http://schemas.openxmlformats.org/package/2006/relationships")
            if self.mode != OpenMode.ReadOnly:
                self._updateRels()

    def close(self):
        self.flush()
        self.zipfile.close()

    def flush(self):
        #Zipfile doesn't need flushing.
        pass

    def getStream(self, virtual_path):
        if self.mode == OpenMode.WriteOnly and virtual_path not in self.zipfile.namelist(): #File doesn't exist yet.
            self.zipfile.writestr(virtual_path, "")
            #TODO: Add manifest.

        if self.mode == OpenMode.WriteOnly: #Instead of appending, we want to overwrite this file completely.
            subfile_mode = "w"
        else:
            subfile_mode = self.mode.value
        return self.zipfile.open(virtual_path, subfile_mode)

    def toByteArray(self, offset: int = 0, count: int = -1):
        with open(self.zipfile.filename, "b") as f:
            if offset > 0:
                f.seek(offset)
            return f.read(count)

    ##  When an element is added to the relations_element, we should update the
    #   rels file in the archive.
    #
    #   Make sure that self.relations_element is up to date first, then call
    #   this update function to actually update it in the file.
    def _updateRels(self):
        self.zipfile.writestr(self.rels_file, ET.tostring(self.xml_header) + "\n" + ET.tostring(self.relations_element))

    ##  When a content type is added to content_types_element, we should update
    #   the content types file in the archive.
    #
    #   Make sure that self.content_types_element is up to date first, then call
    #   this update function to actually update it in the file.
    def _updateContentTypes(self):
        self.zipfile.writestr(self.content_types_file, ET.tostring(self.xml_header) + "\n" + ET.tostring(self.content_types_element))