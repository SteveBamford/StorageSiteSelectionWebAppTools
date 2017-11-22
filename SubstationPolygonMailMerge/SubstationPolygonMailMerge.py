import arcpy
import os
import sys
import datetime
import csv
import pyodbc

class LandownerDetails:

    def __init__(self, polygon_name, title_number, tenure, landowner, address_text, site_location):
        self._polygon_name = polygon_name
        self._title_number = title_number
        self._tenure= tenure
        self._landowner = landowner.title()

        self._address_list = list()
        for address_element in address_text.split(','):
            self._address_list.append(address_element)

        self._site_location = site_location

    @property
    def polygon_name(self):
        return self._polygon_name

    @property
    def title_number(self):
        return self._title_number

    @property
    def tenure(self):
        return self._tenure

    @property
    def landowner(self):
        return self._landowner

    @property
    def site_location(self):
        return self._site_location

    @property
    def address1(self):
        if len(self._address_list) >= 1:
            return self._address_list[0]
        else:
            return ''

    @property
    def address2(self):
        if len(self._address_list) >= 2:
            return self._address_list[1]
        else:
            return ''

    @property
    def address3(self):
        if len(self._address_list) >= 3:
            return self._address_list[2]
        else:
            return ''
    @property
    def address4(self):
        if len(self._address_list) >= 4:
            return self._address_list[3]
        else:
            return ''

    @property
    def address5(self):
        if len(self._address_list) >= 5:
            return self._address_list[4]
        else:
            return ''

    @property
    def address6(self):
        if len(self._address_list) >= 6:
            return self._address_list[5]
        else:
            return ''

def main():
    settings_dictionary = create_settings_dictionary()
    create_mail_merge_csv(settings_dictionary)

def create_settings_dictionary():

    debug = False #debug = True
    settings_dictionary = dict()
    settings_dictionary["OutputFolder"] = r'\\kl-fs-003\GIS_Storage\Projects\ENERGY_STORAGE\SITE_SELECTION\Outbox'

    if (debug == True):
        output_message("Running in debug mode")
        settings_dictionary["OutputFolder"] = r'\\kl-fs-003\GIS_Storage\Personal\SBamford\StorageSiteSelection\MailMerge'

    settings_dictionary["DateTimeStamp"] = get_current_timestamp()
    outputCsvFileName = "MailMerge_%s.csv" %(settings_dictionary["DateTimeStamp"])
    settings_dictionary["outputCsvFilePath"] = os.path.join(settings_dictionary["OutputFolder"],outputCsvFileName)

    return settings_dictionary

def get_current_timestamp():
    strDateFormat = '%Y%m%d'
    strNewTimeStamp = datetime.date.today().strftime(strDateFormat)
    hour = datetime.datetime.utcnow().strftime('%H')
    minute = datetime.datetime.utcnow().strftime('%M')

    strNewTimeStamp = strNewTimeStamp + "_" + hour + minute

    return strNewTimeStamp

def create_mail_merge_csv(settings_dictionary):
    landowner_details_list = get_landowner_details_list_from_view(settings_dictionary)
    csv_line_list = get_csv_line_list(landowner_details_list)
    write_csv_file(settings_dictionary, csv_line_list)
    output_warning(r'Created mail merge file {}'.format(settings_dictionary["outputCsvFilePath"]))

def get_landowner_details_list_from_view(settings_dictionary):
    landowner_details_list = list()
    try:
        conn = pyodbc.connect(
        r'DRIVER={SQL Server};'
        r'SERVER=kl-sql-005;'
        r'DATABASE=GeoDB_UK;'
        r'UID=sde;'
        r'PWD=sde'
        )

        cursor = conn.cursor()

        cursor.execute(sql_for_view_call())
        for row in cursor.fetchall():
            if (row[0]):
                polygon_name = row[0].strip()
                title_number = row[1]
                tenure = row[2]
                proprietor = row[3]
                address = row[4]
                landowner_details_list = add_landowner_details(landowner_details_list, polygon_name, title_number, tenure, proprietor, address)

        conn.close()

        return landowner_details_list

    except Exception as e:
        output_error(e)
        conn.close()

def sql_for_view_call():
    return 'SELECT polygon.[Site_Identifier], land.Title_Number, land.Tenure, land.Proprietor, land.[Address], land.Revision_Date, land.NewSiteID FROM [sde].[tblStoragePolygonIdToLandRegistryIdMapping] map INNER JOIN [sde].[GB_STORAGE_PROPERTY_SKETCH_LAYER] polygon ON map.Storage_Polygon_ID = polygon.[OBJECTID] INNER JOIN [sde].[ENG_Land_Registry_Parcels_evw] land ON map.Land_Registry_ID = land.OBJECTID WHERE polygon.Valid = 1 ORDER BY Site_Identifier'

def add_landowner_details(landowner_details_list, polygon_name, title_number, tenure, proprietor, site_location):
    for proprietor_details_text in proprietor.split(' AND '):
        split_text = proprietor_details_text.strip().split('  ')
        landowner = split_text[0]
        if len(split_text) >= 2:
            address_text = split_text[1]
        else:
            address_text = ''
        landowner_details = LandownerDetails(polygon_name, title_number, tenure, landowner, address_text, site_location)
        landowner_details_list.append(landowner_details)
    return landowner_details_list

def get_csv_line_list(landowner_details_list):
    csv_line_list = list()
    csv_line_list.append(['Substation','Title Number','Tenure','Name Prefix','Landowner first name','Address 1','Address 2','Address 3','Address 4','Address 5','Address 6','Location of site'])
    for landowner_details in landowner_details_list:
        csv_line_list.append(csv_line_from_landowner_details(landowner_details))
    return csv_line_list

def csv_line_from_landowner_details(landowner_details):
    csv_line = [landowner_details.polygon_name, landowner_details.title_number, landowner_details.tenure, '', landowner_details.landowner, landowner_details.address1, landowner_details.address2, landowner_details.address3, landowner_details.address4, landowner_details.address5, landowner_details.address6, landowner_details.site_location ]
    return csv_line

def write_csv_file(settings_dictionary, csv_line_list):
    output_message(r'Writing {}...'.format(settings_dictionary["outputCsvFilePath"]))
    with open(settings_dictionary["outputCsvFilePath"], 'w') as csvfile:
        csv_file_writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
        for csv_line in csv_line_list:
            csv_file_writer.writerow(csv_line)

def output_message(message):
    print message
    arcpy.AddMessage(message)

def output_warning(message):
    print message
    arcpy.AddWarning(message)

def output_error(message):
    print message
    arcpy.AddError(message)

if __name__ == '__main__':
    main()
