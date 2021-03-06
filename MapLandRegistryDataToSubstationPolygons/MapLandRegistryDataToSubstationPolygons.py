import arcpy
import os
from datetime import datetime
import pyodbc

Debug = False

class SiteIdentifierMappingDetails:

    def __init__(self, polygon_id):
        self._polygon_id = polygon_id
        self._title_number_list = list()
        self._tenure_list = list()
        self._proprietor_list = list()
        self._address_list = list()
        self._land_registry_id_list = list()

    def _contains_details(self, title_number, tenure, proprietor, address):
        for index in range(0, len(self._title_number_list)):
            if (self._title_number_list[index] == title_number and self._tenure_list[index] == tenure and self._proprietor_list[index] == proprietor and self._address_list[index] == address):
                return True
        return False

    def _add_title_number(self, title_number):
        self._title_number_list.append(title_number)

    def _add_tenure(self, tenure):
        self._tenure_list.append(tenure)

    def _add_proprietor(self, proprietor):
        self._proprietor_list.append(proprietor)

    def _add_address(self, address):
        self._address_list.append(address)

    def _add_land_registry_id(self, id):
        self._land_registry_id_list.append(id)

    @property
    def length(self):
        return len(self._title_number_list)

    @property
    def polygon_id(self):
        return self._polygon_id


    def get_title_number(self, number):
        return self._title_number_list[number]

    def get_tenure(self, number):
        return self._tenure_list[number]

    def get_proprietor(self, number):
        return self._proprietor_list[number]

    def get_address(self, number):
        return self._address_list[number]

    def get_land_registry_id(self, number):
        return self._land_registry_id_list[number]

def main():

    try:
        mapping_shapefile_path = r'\\kl-fs-003\gis_storage\Projects\ENERGY_STORAGE\SITE_SELECTION\Python\Temporary\mapping.shp'

        create_mapping_shapefile(mapping_shapefile_path)

        populate_mapping_database_tables_from_shapefile(mapping_shapefile_path)

    except Exception as e:
        output_error(e)

def create_mapping_shapefile(mapping_shapefile_path):

    if (mapping_shapefile_path.endswith('.shp') and os.path.isfile(mapping_shapefile_path)):
        output_message("Deleting existing shapefile {}...".format(mapping_shapefile_path))
        arcpy.Delete_management(mapping_shapefile_path)

    temp_polygon_path = r'\\kl-fs-003\gis_storage\Projects\ENERGY_STORAGE\SITE_SELECTION\Python\Temporary\filtered_polygon_lyr'
    temp_land_reg_path = r'\\kl-fs-003\gis_storage\Projects\ENERGY_STORAGE\SITE_SELECTION\Python\Temporary\land_reg_lyr'

    output_message("Creating local polygon layer...")
    arcpy.MakeFeatureLayer_management(in_features=r'\\kl-fs-003\gis_storage\Ancillary\RES_software_Services\GeoDB_UK.sde\GeoDB_UK.SDE.GB_Storage_Property_Sketch_Layer', out_layer=temp_polygon_path, where_clause="Valid = 1 AND Download_Land_Data = 1")
    output_message("Creating local Land Registry layer...")
    arcpy.MakeFeatureLayer_management(in_features=r'\\kl-fs-003\gis_storage\Ancillary\RES_software_Services\GeoDB_UK.sde\GeoDB_UK.SDE.ENG_Land_Registry_Parcels',out_layer=temp_land_reg_path, where_clause="", workspace="", field_info="OBJECTID OBJECTID VISIBLE NONE;TSLID TSLID VISIBLE NONE;TSLFgnKey TSLFgnKey VISIBLE NONE;TSLType TSLType VISIBLE NONE;LR_TITLE LR_TITLE VISIBLE NONE;Title_Number Title_Number VISIBLE NONE;Tenure Tenure VISIBLE NONE;Proprietor Proprietor VISIBLE NONE;Address Address VISIBLE NONE;Revision_Date Revision_Date VISIBLE NONE;NewSiteID NewSiteID VISIBLE NONE;SHAPE SHAPE VISIBLE NONE;SHAPE.STArea() SHAPE.STArea() VISIBLE NONE;SHAPE.STLength() SHAPE.STLength() VISIBLE NONE")

    output_message("Creating shapefile: {}...".format(mapping_shapefile_path))
    arcpy.Intersect_analysis(in_features="{} #;{} #".format(temp_polygon_path, temp_land_reg_path), out_feature_class=mapping_shapefile_path, join_attributes="ALL", cluster_tolerance="-1 Unknown", output_type="INPUT")

    output_message("Removing local polygon layer...")
    arcpy.Delete_management(temp_polygon_path)
    output_message("Removing local Land Registry layer...")
    arcpy.Delete_management(temp_land_reg_path)

def populate_mapping_database_tables_from_shapefile(mapping_shapefile_path):

    output_message("Populate mapping database tables...")

    clear_id_mapping_table()

    fields = ['FID_GB_Sto', 'Site_Ident', 'Title_Numb', 'Tenure', 'Proprietor', 'Address', 'Revision_D', 'FID_ENG_La']

    ## Create dictionary of mapping data
    previous_polygon_oid = -1
    mapping_dictionary = dict()
    for row in arcpy.da.SearchCursor(mapping_shapefile_path, fields):
        polygon_oid = row[0]
        site_identifier = row[1]
        title_number = row[2]
        tenure = row[3]
        proprietor = row[4]
        address = row[5]
        revision = row[6]
        land_registry_id = row[7]
        if not polygon_oid in mapping_dictionary:
            mapping_dictionary[polygon_oid] = SiteIdentifierMappingDetails(polygon_oid)
        # Avoid adding duplicates (title number, tenure, proprietor and address are all the same
        if not mapping_dictionary[polygon_oid]._contains_details(title_number, tenure, proprietor, address):
            mapping_dictionary[polygon_oid]._add_title_number(title_number)
            mapping_dictionary[polygon_oid]._add_tenure(tenure)
            mapping_dictionary[polygon_oid]._add_proprietor(proprietor)
            mapping_dictionary[polygon_oid]._add_address(address)
            mapping_dictionary[polygon_oid]._add_land_registry_id(land_registry_id)

    for key in mapping_dictionary:
        add_site_identifier_mapping_details_to_database(mapping_dictionary[key])
        add_id_mapping_details_to_database(mapping_dictionary[key])

def add_site_identifier_mapping_details_to_database(mapping_details):
    length = mapping_details.length
    polygon_oid = mapping_details.polygon_id


    for index in range(0, 15):
        if (index < length):
            sql = generate_sql_for_tblStoragePolygonToLandRegistryMapping(
                polygon_oid,
                index + 1,
                "'{}'".format(mapping_details.get_title_number(index)),
                "'{}'".format(make_text_sql_compliant(mapping_details.get_tenure(index))),
                "'{}'".format(make_text_sql_compliant(mapping_details.get_proprietor(index))),
                "'{}'".format(make_text_sql_compliant(mapping_details.get_address(index))))
        else:
            sql = generate_sql_for_tblStoragePolygonToLandRegistryMapping(
                polygon_oid,
                index + 1,
                "NULL",
                "NULL",
                "NULL",
                "NULL")
        execute_sql_on_tblStoragePolygonToLandRegistryMapping(sql)

    if (length >= 16):
        output_warning("Too many mapping items for polygon ID {} ({} found)".format(mapping_details.polygon_id, index + 1))
    else:
        output_message('{} mapping items added for polygon ID {}'.format(length, mapping_details.polygon_id))

def generate_sql_for_tblStoragePolygonToLandRegistryMapping(polygon_oid, mapping_number, title_number, tenure, proprietor, address):
    return "UPDATE [sde].[tblStoragePolygonToLandRegistryMapping] SET [Title_Number_{}] = {} ,[Tenure_{}] = {}, [Proprietor_{}] = {},[Address_{}] = {} WHERE [Storage_Polygon_ID] = {}".format(
        mapping_number, title_number,
        mapping_number, tenure,
        mapping_number, proprietor,
        mapping_number, address,
        polygon_oid)

def make_text_sql_compliant(input_text):
    return input_text.replace("'", "`")

def execute_sql_on_tblStoragePolygonToLandRegistryMapping(sql):
    try:
        conn = pyodbc.connect(
        r'DRIVER={SQL Server};'
        r'SERVER=kl-sql-005;'
        r'DATABASE=GeoDB_UK;'
        r'UID=sde;'
        r'PWD=sde'
        )

        cursor = conn.cursor()

        table_name = "tblStoragePolygonToLandRegistryMapping"

        cursor.execute(sql)
        conn.commit()

        conn.close()
    except Exception as e:
        output_error(e)
        conn.close()

def clear_id_mapping_table():
    execute_sql_on_tblStoragePolygonIdToLandRegistryIdMapping(get_clear_tblStoragePolygonIdToLandRegistryIdMapping_sql())

def add_id_mapping_details_to_database(mapping_details):
    length = mapping_details.length
    polygon_oid = mapping_details.polygon_id

    if length > 0:
        for index in range(0, length):
            add_id_mapping_table_entry(polygon_oid, mapping_details.get_land_registry_id(index))

def get_clear_tblStoragePolygonIdToLandRegistryIdMapping_sql():
    return 'DELETE FROM tblStoragePolygonIdToLandRegistryIdMapping'

def add_id_mapping_table_entry(polygon_oid, land_registry_id):
    execute_sql_on_tblStoragePolygonIdToLandRegistryIdMapping(get_add_ids_tblStoragePolygonIdToLandRegistryIdMapping_sql(polygon_oid, land_registry_id))

def get_add_ids_tblStoragePolygonIdToLandRegistryIdMapping_sql(polygon_oid, land_registry_id):
    return 'INSERT INTO [sde].[tblStoragePolygonIdToLandRegistryIdMapping] ([Storage_Polygon_ID],[Land_Registry_ID]) VALUES ({} ,{})'.format(polygon_oid, land_registry_id)

def execute_sql_on_tblStoragePolygonIdToLandRegistryIdMapping(sql):
    try:
        conn = pyodbc.connect(
        r'DRIVER={SQL Server};'
        r'SERVER=kl-sql-005;'
        r'DATABASE=GeoDB_UK;'
        r'UID=sde;'
        r'PWD=sde'
        )

        cursor = conn.cursor()

        table_name = "tblStoragePolygonIdToLandRegistryIdMapping"

        cursor.execute(sql)
        conn.commit()

        conn.close()
    except Exception as e:
        output_error(e)
        conn.close()

def output_message(message):
    if (Debug == True):
        print message
    arcpy.AddMessage(message)

def output_warning(message):
    if (Debug == True):
        print message
    arcpy.AddWarning(message)

def output_error(message):
    if (Debug == True):
        print message
    arcpy.AddError(message)

if __name__ == '__main__':
    main()
