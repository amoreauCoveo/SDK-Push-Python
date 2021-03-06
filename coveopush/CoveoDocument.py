#-------------------------------------------------------------------------------------
# CoveoDocument
#-------------------------------------------------------------------------------------
# Contains the CoveoDocument class
#   A CoveoDocument will be pushed to the push source
#-------------------------------------------------------------------------------------
import base64
import io
from urllib.parse import urlparse
from . import CoveoConstants
from . import CoveoPermissions
import json
import re
import logging
import zlib
import os.path
from datetime import datetime

#---------------------------------------------------------------------------------
def isBase64(s):
  """
  isBase64. 
  Checks if string is base64 encoded.
  Returns True/False
  """
  try:
      return base64.b64encode(base64.b64decode(s)) == s
  except Exception:
      return False

#---------------------------------------------------------------------------------
def Validate( obj ):
  """
  Validate. 
  Validates if all properties on the CoveoDocument are properly set. 
  Returns True/False, Error
  """
  result = True
  error = ''
  if obj.DocumentId == '':
    error = 'DocumentId is empty |'
    result = False
  #data or CompressedBinaryData should be set, not both
  if obj.Data and obj.CompressedBinaryData:
    error += 'Both Data and CompressedBinaryData are set |'
    result = False
  #Validate documentId, should be a valid url
  try:
    urlparse(obj.DocumentId)
  except:
    error += 'DocumentId is not a valid URL |'
    result = False
  if obj.Title == '':
    error += 'Title is empty |'
    result = False
  return result, error


#---------------------------------------------------------------------------------
def Error(log, err):
  log.logger.info(err)
  raise Exception(err)

#---------------------------------------------------------------------------------
class BatchDocument:
  """
  class BatchDocument. 
  Class to hold the Batch Document.
  """
  AddOrUpdate = []
  Delete = []

#---------------------------------------------------------------------------------
class DocumentToDelete:
  """
  class DocumentToDelete. 
  Class to hold the Document To Delete.
  It should consist of the DocumentId (URL) only."""
  #The unique document identifier for the source, must be the document URI.
  DocumentId = ''
  Title = ''

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def __init__(self, p_DocumentId:str):
    self.DocumentId = p_DocumentId
    self.Title = p_DocumentId

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def ToJson( self ):
    """ToJson, returns JSON for push.
    Puts all metadata and other fields into clean"""
    #Check if empty

    all = dict()
    all["DocumentId"] = self.DocumentId
    return all

#---------------------------------------------------------------------------------
class Document:
  """
  class Document. 
  Class to hold the Document To Push.
  Mandatory properties: DocumentId (URL) and Title."""
  Data = ''
  Date = ''
  DocumentId = ''
  Title = ''
  ModifiedDate = ''
  IndexedDate = ''
  CompressedBinaryData = ''
  CompressedBinaryDataFileId = ''
  CompressionType = ''
  FileExtension = ''
  ParentId = ''
  ClickableUri = ''
  Author = ''
  Permissions = []
  MetaData = {}

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def __init__(self, p_DocumentId:str):
    """
    class Document constructor.
    :arg p_DocumentId: Document Id, valid URL
    """
    self.DocumentId = p_DocumentId
    self.Permissions = []
    self.MetaData = {}
    self.Data = ''
    self.Date = ''
    self.Title = ''
    self.ModifiedDate = ''
    self.IndexedDate = ''
    self.CompressedBinaryData = ''
    self.CompressedBinaryDataFileId = ''
    self.CompressionType = ''
    self.FileExtension = ''
    self.ParentId = ''
    self.ClickableUri = ''
    self.Author = ''
    self.logger = logging.getLogger('CoveoDocument')

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def ToJson( self ):
    """
    ToJson, returns JSON for push.
    Puts all metadata and other fields into a clean JSON object"""
    self.logger.debug('ToJson')
    #Check if empty

    all = dict()
    if self.Data:
      all["Data"] = self.Data
    all["Date"] = self.Date
    all["DocumentId"] = self.DocumentId
    all["Title"] = self.Title
    all["ModifiedDate"] = self.ModifiedDate
    all["IndexedDate"] = self.IndexedDate
    if self.CompressedBinaryData:
      all["CompressedBinaryData"] = self.CompressedBinaryData
    if self.CompressedBinaryDataFileId:
      all["CompressedBinaryDataFileId"] = self.CompressedBinaryDataFileId
    all["CompressionType"] = self.CompressionType
    all["FileExtension"] = self.FileExtension
    all["ParentId"] = self.ParentId
    all["ClickableUri"] = self.ClickableUri
    all["Author"] = self.Author
    if self.Permissions:
      all["Permissions"] = self.Permissions
    for meta in self.MetaData:
       all[meta] = self.MetaData[meta]
    return all


  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def SetData( self, p_Data: str ):
    """
    SetData. 
    Sets the Data (plain text) property.
    :arg p_Data: str, sets the Data (Plain Text) 
    """

    self.logger.debug('SetData')
    #Check if empty
    if (p_Data==''):
      Error(self, "SetData: value not set")

    self.Data = p_Data

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def SetDate( self, p_Date: datetime ):
    """
    SetDate. 
    Sets the date property.
    :arg p_Date: datetime, set the date
    """

    self.logger.debug('SetDate')
    #Check if empty
    if (p_Date==''):
      Error(self, "SetDate: value not set")

    self.Date = p_Date.isoformat()

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def SetModifiedDate( self, p_Date: datetime ):
    """
    SetModifiedDate. 
    Sets the ModifiedDate property.
    :arg p_Date: datetime, set the ModifiedDate date
    """

    self.logger.debug('SetModifiedDate')
    #Check if empty
    if (p_Date==''):
      Error(self, "SetModifiedDate: value not set")

    self.ModifiedDate = p_Date.isoformat()

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def SetDateWithString( self, p_Date: str, p_Format: str ):
    """
    SetDateWithString. 
    Sets the Date property, based on the p_Format ("%Y-%m-%d") supplied.
    :arg p_Date: str, set the date
    :arg p_Format: str, set the format to use
    """

    self.logger.debug('SetDateWithString')
    #Check if empty
    if (p_Date==''):
      Error(self, "SetDateWithString: value not set")

    self.Date = datetime.strptime(p_Date, p_Format).isoformat()

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def SetCompressedEncodedData( self, p_CompressedEncodedData: str, p_CompressionType: CoveoConstants.Constants.CompressionType = CoveoConstants.Constants.CompressionType.ZLIB ):
    """
    SetCompressedEncodedData. 
    Sets the CompressedBinaryData property.
    Make sure to set the proper CompressionType and Base64 encode the CompressedEncodedData.
    :arg p_CompressedEncodedData: str, Encoded Data (base64 ecoded)
    :arg p_CompressionType: CoveoConstants.Constants.CompressionType (def: ZLIB), CompressionType to Use
    """

    self.logger.debug('SetCompressedEncodedData')
    #Check if empty
    if (p_CompressedEncodedData==''):
      Error(self, "SetCompressedEncodedData: value not set")
    
    #Check if base64 encoded
    if not (isBase64(p_CompressedEncodedData)):
      Error(self, "SetCompressedEncodedData: value must be base64 encoded.")

    self.CompressedBinaryData = p_CompressedEncodedData
    self.CompressedBinaryDataFileId = ''
    self.CompressionType = p_CompressionType.value

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def SetContentAndZLibCompress( self, p_Content: str ):
    """
    SetContentAndCompress. 
    Sets the CompressedBinaryData property, it will ZLIB compress the string and base64 encode it
    :arg p_Content: str, string
    """

    self.logger.debug('SetContentAndCompress')
    #Check if empty
    if (p_Content==''):
      Error(self, "SetContentAndCompress: value not set")

    compresseddata = zlib.compress(p_Content.encode('utf8'), zlib.Z_BEST_COMPRESSION) 
    encodeddata = base64.b64encode(compresseddata).decode('ascii')


    self.CompressedBinaryData = encodeddata
    self.CompressedBinaryDataFileId = ''
    self.CompressionType = CoveoConstants.Constants.CompressionType.ZLIB.value

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def GetFileAndCompress( self, p_FilePath: str ):
    """
    GetFileAndCompress. 
    Gets the file, compresses it (ZLIB), base64 encode it, set the filetype
    :arg p_FilePath: str, valid file
    """

    self.logger.debug('GetFileAndCompress')
    #Check if empty
    if (p_FilePath==''):
      Error(self, "GetFileAndCompress: value not set")

    #Check if file exists
    if not (os.path.isfile):
      Error(self, "GetFileAndCompress: file does not exists "+p_FilePath)

    with open(p_FilePath, mode='rb') as file: # b is important -> binary
      fileContent = file.read()
      compresseddata = zlib.compress(fileContent, zlib.Z_BEST_COMPRESSION)
      encodeddata = base64.b64encode(compresseddata).decode('ascii') 

    #Get the extension
    __, file_extension = os.path.splitext(p_FilePath)
    self.FileExtension = file_extension
    self.CompressedBinaryData = encodeddata
    self.CompressedBinaryDataFileId = ''
    self.CompressionType = CoveoConstants.Constants.CompressionType.ZLIB.value

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def SetCompressedDataFileId( self, p_CompressedDataFileId: str):
    """
    SetCompressedDataFileId. 
    Sets the CompressedBinaryDataFileId property.
    :arg p_CompressedDataFileId: str, the fileId retrieved by the GetLargeFileContainer call
    """

    self.logger.debug('SetCompressedDataFileId')
    #Check if empty
    if (p_CompressedDataFileId==''):
      Error(self, "SetCompressedDataFileId: value not set")

    self.CompressedBinaryData = ''
    self.Data = ''
    self.CompressedBinaryDataFileId = p_CompressedDataFileId

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def AddMetadata(self, p_Key: str, p_Value: object):
    """
    AddMetadata. 
    Sets the metadata.
    :arg p_Key: str, the key value to set
    :arg p_Value: object, the value or object to set (str or list)
    """

    self.logger.debug('AddMetadata')
    #Check if empty
    if (p_Key==''):
      Error(self, "AddMetadata: key not set")

    #Check if in reserved keys 
    if (p_Key.lower() in [key.lower() for key in CoveoConstants.Constants.s_DocumentReservedKeys] ):
      Error(self, "AddMetadata: "+p_Key+ " is a reserved field and cannot be set as metadata.")

    #Check if empty
    if (p_Value=='' or p_Value==None):
      Error(self, "AddMetadata: value not set")

    self.MetaData[p_Key.lower()] = p_Value

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  def SetAllowedAndDeniedPermissions(self, p_AllowedPermissions: [], p_DeniedPermissions: [], p_AllowAnonymous: bool = False):
    """
    SetAllowedAndDeniedPermissions. 
    Sets the permissions on the document.
    :arg p_AllowedPermissions: list of PermissionIdentities which have access
    :arg p_DeniedPermissions: list of PermissionIdentities which do NOT have access
    :arg p_AllowAnonymous: (def: False) if Anonymous access is allowed
    """

    self.logger.debug('SetAllowedAndDeniedPermissions')
    #Check if empty
    if (p_AllowedPermissions==None):
      Error(self, "SetAllowedAndDeniedPermissions: AllowedPermissions not set")
    if (p_DeniedPermissions==None):
      Error(self, "SetAllowedAndDeniedPermissions: DeniedPermissions not set")

    simplePermissionLevel = CoveoPermissions.DocumentPermissionLevel('Level1')

    simplePermissionSet = CoveoPermissions.DocumentPermissionSet('Set1')
    simplePermissionSet.AddAllowedPermissions( p_AllowedPermissions )
    simplePermissionSet.AddDeniedPermissions( p_DeniedPermissions ) 
    simplePermissionSet.AllowAnonymous = p_AllowAnonymous

    simplePermissionLevel.AddPermissionSet(simplePermissionSet)

    self.Permissions.append(simplePermissionLevel)

