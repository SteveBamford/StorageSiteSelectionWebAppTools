import arcpy
import os
import sys
import datetime
import csv

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
    settings_dictionary["InputDatabase"] = r'\\kl-fs-003\GIS_Storage\Ancillary\RES_software_Services\GeoDB_UK.sde'
    settings_dictionary["InputPolygonFeatureClass"] = 'GeoDB_UK.sde.GB_STORAGE_SUBSTATION_SKETCH_POLYGONS'
    settings_dictionary["PolygonFeatureClassPath"] = os.path.join(settings_dictionary["InputDatabase"],settings_dictionary["InputPolygonFeatureClass"])

    if (debug == True):
        output_message("Running in debug mode")
        settings_dictionary["OutputFolder"] = r'\\kl-fs-003\GIS_Storage\Personal\SBamford\StorageSiteSelection\MailMerge'

    settings_dictionary["DateTimeStamp"] = get_current_timestamp()
    outputCsvFileName = "MailMerge_%s.csv" %(settings_dictionary["DateTimeStamp"])
    settings_dictionary["outputCsvFilePath"] = os.path.join(settings_dictionary["OutputFolder"],outputCsvFileName)

    settings_dictionary["polygonValidWhereClause"] = 'Valid = 1 AND TitleNumber1 IS NOT NULL'

    return settings_dictionary

def get_current_timestamp():
    strDateFormat = '%Y%m%d'
    strNewTimeStamp = datetime.date.today().strftime(strDateFormat)
    hour = datetime.datetime.utcnow().strftime('%H')
    minute = datetime.datetime.utcnow().strftime('%M')

    strNewTimeStamp = strNewTimeStamp + "_" + hour + minute

    return strNewTimeStamp

def create_mail_merge_csv(settings_dictionary):
    landowner_details_list = get_landowner_details_list(settings_dictionary)
    csv_line_list = get_csv_line_list(landowner_details_list)
    write_csv_file(settings_dictionary, csv_line_list)
    output_warning(r'Created mail merge file {}'.format(settings_dictionary["outputCsvFilePath"]))

def get_landowner_details_list(settings_dictionary):
    landowner_details_list = list()

    output_message('Getting landowner details...')
    fields = ['Site_Identifier','Valid','SubStation',
        'TitleNumber1','Tenure1','Proprietor1','Address1',     #3  to 6
        'TitleNumber2','Tenure2','Proprietor2','Address2',     #7  to 10
        'TitleNumber3','Tenure3','Proprietor3','Address3',     #11 to 14
        'TitleNumber4','Tenure4','Proprietor4','Address4',     #15 to 18
        'TitleNumber5','Tenure5','Proprietor5','Address5',     #19 to 22
        'TitleNumber6','Tenure6','Proprietor6','Address6',     #23 to 26
        'TitleNumber7','Tenure7','Proprietor7','Address7',     #27 to 30
        'TitleNumber8','Tenure8','Proprietor8','Address8',     #31 to 34
        'TitleNumber9','Tenure9','Proprietor9','Address9',     #35 to 38
        'TitleNumber10','Tenure10','Proprietor10','Address10', #39 to 42
        'TitleNumber11','Tenure11','Proprietor11','Address11', #43 to 46
        'TitleNumber12','Tenure12','Proprietor12','Address12', #47 to 50
        'TitleNumber13','Tenure13','Proprietor13','Address13', #51 to 52
        'TitleNumber14','Tenure14','Proprietor14','Address14', #55 to 58
        'TitleNumber15','Tenure15','Proprietor15','Address15', #59 to 62
        'TitleNumber16','Tenure16','Proprietor16','Address16'] #63 to 66

    for row in arcpy.da.SearchCursor(settings_dictionary["PolygonFeatureClassPath"], fields):
        if (row[0]):
            polygon_name = row[0].strip()
            valid_row = row[1]
            title_number_index = 3
            if (valid_row):
                while (title_number_index <= 63):
                    if (row[title_number_index]):
                        landowner_details_list = add_landowner_details(landowner_details_list, polygon_name, row[title_number_index].strip(), row[title_number_index+1].strip(), row[title_number_index+2].strip(), row[title_number_index+3].strip())
                    title_number_index = title_number_index + 4
            else:
                output_warning('Invalid row for {}'.format(polygon_name))
        else:
            output_warning('Polygon data found with no Site_Identifier!')
    return landowner_details_list

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
    with open(settings_dictionary["outputCsvFilePath"], 'wb') as csvfile:
        csv_file_writer = csv.writer(csvfile)##, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
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
