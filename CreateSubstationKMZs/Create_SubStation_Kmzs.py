import arcpy
import os
import sys
import datetime

Debug = False

def main():
    settings_dictionary = create_settings_dictionary()
    create_substation_kmzs(settings_dictionary)

def create_settings_dictionary():

    debug = False #debug = True
    settings_dictionary = dict()
    settings_dictionary["OutputFolder"] = r'\\kl-fs-003\GIS_Storage\Projects\ENERGY_STORAGE\SITE_SELECTION\Outbox\SubStationKMZs'
    settings_dictionary["InputDatabase"] = r'\\kl-fs-003\GIS_Storage\Ancillary\RES_software_Services\GeoDB_UK.sde'
    settings_dictionary["InputSubstationFeatureClass"] = 'GeoDB_UK.SDE.GB_Storage_Substation_201708' ## Use same data as UK_I_Storage/GB_Storage_Substation_Review_201708, which is from \\kl-fs-003\GIS_Storage\Personal\SBamford\StorageSiteSelection\Substation Review 201708.mxd
    settings_dictionary["InputPolygonFeatureClass"] = 'GeoDB_UK.sde.GB_STORAGE_SUBSTATION_SKETCH_POLYGONS_201708' ## Use same data as UK_I_Storage/GB_Storage_Polygon_View_Substation_Review_201708, which is from \\kl-fs-003\GIS_Storage\Personal\SBamford\StorageSiteSelection\Substation Review 201708 Polygon View.mxd
    settings_dictionary["styleLYR"] = r'\\kl-fs-003\GIS_Storage\Ancillary\Templates\Feature_Templates\Layers\Land_Registry_Redline_Boundary.lyr'
    settings_dictionary["SubstationFeatureClassPath"] = os.path.join(settings_dictionary["InputDatabase"],settings_dictionary["InputSubstationFeatureClass"])
    settings_dictionary["PolygonFeatureClassPath"] = os.path.join(settings_dictionary["InputDatabase"],settings_dictionary["InputPolygonFeatureClass"])
    settings_dictionary["BaseTemplateMxd"] = r'\\kl-fs-003\GIS_Storage\Projects\ENERGY_STORAGE\SITE_SELECTION\Templates\BaseTemplate.mxd'
    settings_dictionary["BaseTemplateSubstationLayer"] = r"\\kl-fs-003\GIS_Storage\Projects\ENERGY_STORAGE\SITE_SELECTION\Templates\SubstationBaseLayer.lyr"
    settings_dictionary["BaseTemplatePolygonsLayer"] = r"\\kl-fs-003\GIS_Storage\Projects\ENERGY_STORAGE\SITE_SELECTION\Templates\PolygonsBaseLayer.lyr"
    strNewTimeStamp = get_current_timestamp()

    if (Debug == True):
        output_message("Running in debug mode")
        settings_dictionary["OutputFolder"] = r'\\kl-fs-003\GIS_Storage\Personal\SBamford\StorageSiteSelection\KMZTesting'

    settings_dictionary["DateTimeStamp"] = get_current_timestamp()

    settings_dictionary["subStationMinimumStatus"] = 3
    settings_dictionary["subStationStatusWhereClause"] = "Status >= %s" %(settings_dictionary["subStationMinimumStatus"])
    settings_dictionary["polygonValidWhereClause"] = 'Valid = 1'
    settings_dictionary["substationLoopWarningEveryXSubstations"] = 3

    return settings_dictionary

def get_current_timestamp():
    strDateFormat = '%Y%m%d'
    strNewTimeStamp = datetime.date.today().strftime(strDateFormat)
    hour = datetime.datetime.utcnow().strftime('%H')
    minute = datetime.datetime.utcnow().strftime('%M')

    strNewTimeStamp = strNewTimeStamp + "_" + hour + minute

    return strNewTimeStamp

def create_substation_kmzs(settings_dictionary):
    output_warning('Creating substation KMZs in {}'.format(settings_dictionary["OutputFolder"]))
    substation_name_list = get_substation_name_list(settings_dictionary)
    substation_number = 1
    substation_total = len(substation_name_list)
    output_warning('{} substations to be processed...'.format(substation_total))
    for substation_name in substation_name_list:
        if (substation_name):
            process_substation(settings_dictionary, substation_name)
            if (substation_number%settings_dictionary["substationLoopWarningEveryXSubstations"] == 0):
                output_warning('Processed {} out of {}...'.format(substation_number, substation_total))
        else:
            output_warning('Null substation name found for substation {}'.format(substation_number))
        substation_number = substation_number + 1

def process_substation(settings_dictionary, substation_name):
    try:
        create_mxd_for_substation(settings_dictionary, substation_name)
        export_mxd_to_kmz(settings_dictionary, substation_name)
        remove_mxd_for_substation(settings_dictionary, substation_name)
    except Exception as e:
        output_error('Error whilst creating KMZ for {}: {}'.format(substation_name, e))

def get_substation_name_list(settings_dictionary):
    substation_name_list = list()
    output_message("Getting substation list...")

    fields = ['Name', 'Status']
    for row in arcpy.da.SearchCursor(settings_dictionary["SubstationFeatureClassPath"], fields):
        if row[1] >= settings_dictionary["subStationMinimumStatus"]:
            substation_name_list.append(row[0])

    return substation_name_list

def create_mxd_for_substation(settings_dictionary, substation_name):
    output_message("Creating temporary MXD for %s..." %(substation_name))

    arcpy.env.workspace = settings_dictionary["OutputFolder"]
    output_message('Opening base template MXD ({})...'.format(settings_dictionary["BaseTemplateMxd"])) #SDCBDBEUG
    mxd = arcpy.mapping.MapDocument(settings_dictionary["BaseTemplateMxd"])
    output_message('Getting Layers data frame...') #SDCBDBEUG
    data_frame = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]

    substation_layer = substation_layer_name(settings_dictionary, substation_name)
    output_message('Creating substation layer ({})'.format(substation_layer)) #SDCBDBEUG
    arcpy.MakeFeatureLayer_management(
        settings_dictionary["SubstationFeatureClassPath"],
        substation_layer,
        substation_where_clause(settings_dictionary, substation_name))
    substation_layer_object = arcpy.mapping.Layer(substation_layer)
    substation_base_layer = arcpy.mapping.Layer(settings_dictionary["BaseTemplateSubstationLayer"])
    output_message('Updating layer...')  # SDCBDBEUG
    arcpy.mapping.UpdateLayer(data_frame, substation_layer_object, substation_base_layer, True)
    output_message('Adding layer...')  # SDCBDBEUG
    arcpy.mapping.AddLayer(
        data_frame,
        substation_layer_object,
        "Bottom")

    polygons_layer = polygons_layer_name(settings_dictionary, substation_name)
    output_message('Creating polygon layer ({})'.format(polygons_layer)) #SDCBDBEUG
    arcpy.MakeFeatureLayer_management(
        settings_dictionary["PolygonFeatureClassPath"],
        polygons_layer,
        polygons_where_clause(settings_dictionary, substation_name))
    polygons_layer_object = arcpy.mapping.Layer(polygons_layer)
    polygons_base_layer = arcpy.mapping.Layer(settings_dictionary["BaseTemplatePolygonsLayer"])
    output_message('Updating layer...')  # SDCBDBEUG
    arcpy.mapping.UpdateLayer(data_frame, polygons_layer_object, polygons_base_layer, True)
    output_message('Adding layer...')  # SDCBDBEUG
    arcpy.mapping.AddLayer(
        data_frame,
        polygons_layer_object,
        "Bottom")

    mxd_file_path = substation_mxd_file_path(settings_dictionary, substation_name)
    output_message('Saving MXD as ({})...'.format(mxd_file_path))  # SDCBDBEUG
    mxd.saveACopy(mxd_file_path)

def polygons_where_clause(settings_dictionary, substation_name):
    return "SubStation = '%s' AND %s" %(substation_name, settings_dictionary["polygonValidWhereClause"])

def substation_where_clause(settings_dictionary, substation_name):
    return "Name = '%s' AND %s" %(substation_name, settings_dictionary["subStationStatusWhereClause"])

def substation_layer_name(settings_dictionary, substation_name):
    return "%s Substation" %(clean_substation_name(substation_name))

def polygons_layer_name(settings_dictionary, substation_name):
    return "%s Polygons" %(clean_substation_name(substation_name))

def export_mxd_to_kmz(settings_dictionary, substation_name):
    output_message("Creating KMZ for %s..." %(substation_name))
    mxd_file_path = substation_mxd_file_path(settings_dictionary, substation_name)
    kmz_file_path = substation_kmz_file_path(settings_dictionary, substation_name)
    kmz_directory_path = substation_kmz_directory_path(settings_dictionary)

    if (os.path.isdir(kmz_directory_path) == False):
        os.mkdir(kmz_directory_path)
    arcpy.MapToKML_conversion(
        in_map_document=mxd_file_path,
        data_frame="Layers",
        out_kmz_file=kmz_file_path,
        map_output_scale="0",
        is_composite="NO_COMPOSITE",
        is_vector_to_raster="VECTOR_TO_IMAGE",
        extent_to_export="DEFAULT",
        image_size="1024",
        dpi_of_client="96",
        ignore_zvalue="CLAMPED_TO_GROUND")

def remove_mxd_for_substation(settings_dictionary, substation_name):
    output_message("Removing temporary MXD for %s..." %(substation_name))
    mxd_file_path = substation_mxd_file_path(settings_dictionary, substation_name)
    if (os.path.isfile(mxd_file_path)):
        os.remove(mxd_file_path)

def substation_mxd_file_path(settings_dictionary, substation_name):
    return r"%s\Substation_%s_%s.mxd" %(settings_dictionary["OutputFolder"],clean_substation_name(substation_name),settings_dictionary["DateTimeStamp"])

def substation_kmz_directory_path(settings_dictionary):
    return r"%s\%s" %(settings_dictionary["OutputFolder"],settings_dictionary["DateTimeStamp"])

def substation_kmz_file_path(settings_dictionary, substation_name):
    return r"%s\Substation_%s.kmz" %(substation_kmz_directory_path(settings_dictionary),clean_substation_name(substation_name))

def clean_substation_name(substation_name):
    return substation_name.replace('/', '')

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
