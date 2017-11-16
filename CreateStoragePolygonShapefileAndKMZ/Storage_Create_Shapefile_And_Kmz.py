import arcpy
import os
import sys
import datetime
import zipfile
import shutil

def main():
    settings_dictionary = create_settings_dictionary()
    create_shapefile_and_kmz_for_valid_storage_polygons(settings_dictionary)

def create_settings_dictionary():

    debug = False ##debug = True
    settings_dictionary = dict()
    settings_dictionary["OutputFolder"] = r'\\kl-fs-003\GIS_Storage\Ancillary\RES_software_Services\Land_Registry\Outbox'
    settings_dictionary["OutputGDB"] = r'\\kl-fs-003\GIS_Storage\Ancillary\RES_software_Services\Land_Registry\Land_Registry.gdb'
    settings_dictionary["InputDatabase"] = r'\\kl-fs-003\GIS_Storage\Ancillary\RES_software_Services\GeoDB_UK.sde'
    settings_dictionary["InputFeatureClass"] = 'GeoDB_UK.SDE.GB_Storage_Property_Sketch_Layer'
    settings_dictionary["InputFeatureClassView"] = 'GeoDB_UK.sde.GB_STORAGE_SUBSTATION_SKETCH_POLYGONS'
    settings_dictionary["TemplateMXD"] = r"\\kl-fs-003\GIS_Storage\Ancillary\Templates\Map_Document_Templates\Task_Based\Land_Registry_SketchUp_DrawingTemplate.mxd"
    settings_dictionary["styleLYR"] = r'\\kl-fs-003\GIS_Storage\Ancillary\Templates\Feature_Templates\Layers\Land_Registry_Redline_Boundary.lyr'
    settings_dictionary["InputFeatureClassPath"] = os.path.join(settings_dictionary["InputDatabase"],settings_dictionary["InputFeatureClass"])
    settings_dictionary["InputFeatureClassViewPath"] = os.path.join(settings_dictionary["InputDatabase"],settings_dictionary["InputFeatureClassView"])

    strNewTimeStamp = get_current_timestamp()

    strRunName = "StorageSiteSelection"

    if (debug == True):
        output_message("Running in debug mode")
        settings_dictionary["OutputFolder"] = r'\\kl-fs-003\GIS_Storage\Personal\SBamford\ShapefileAndKmzTest\Outbox'
        settings_dictionary["OutputGDB"] = r'\\kl-fs-003\GIS_Storage\Personal\SBamford\ShapefileAndKmzTest\Testing.gdb'

    outputShapeFileFolder = r"%s\LandRegistryShapeFile_%s_%s" %(settings_dictionary["OutputFolder"],strRunName,strNewTimeStamp)
    outputShapeFile = r"%s\LandRegistryShape_%s_%s.shp" %(outputShapeFileFolder,strRunName,strNewTimeStamp)
    outputFeatureClass = r"%s\LandRegistryShape_%s_%s" %(settings_dictionary["OutputGDB"] ,strRunName,strNewTimeStamp)
    outputShapeFileFolderZipped ="%s.zip" %(outputShapeFileFolder)
    outputPDF =r"%s\LandRegistryShape_%s_%s.pdf" %(settings_dictionary["OutputFolder"],strRunName,strNewTimeStamp)
    outputMXD = r"%s\LandRegistryShape_%s_%s.mxd" %(settings_dictionary["OutputFolder"],strRunName,strNewTimeStamp)
    temporaryLayer = r"%s\LandRegistryShape_%s_%s_lyr" %(settings_dictionary["OutputFolder"],strRunName,strNewTimeStamp)
    outputKMZ = r"%s\LandRegistryShape_%s_%s.kmz" %(settings_dictionary["OutputFolder"],strRunName,strNewTimeStamp)

    settings_dictionary["outputShapeFileFolder"] = os.path.join(outputShapeFileFolder)
    settings_dictionary["outputShapeFile"] = os.path.join(outputShapeFile)
    settings_dictionary["outputFeatureClass"] = os.path.join(outputFeatureClass)
    settings_dictionary["outputShapeFileFolderZipped"] = os.path.join(outputShapeFileFolderZipped)
    settings_dictionary["outputPDF"] = os.path.join(outputPDF)
    settings_dictionary["outputMXD"] = os.path.join(outputMXD)
    settings_dictionary["temporaryLayer"] = os.path.join(temporaryLayer)
    settings_dictionary["outputKMZ"] = os.path.join(outputKMZ)
    settings_dictionary["DateTimeStamp"] = get_database_timestamp()
    settings_dictionary["RunIdentifier"] = r"%s_%s" %(strRunName,strNewTimeStamp)

    settings_dictionary["ViewWhereClause"] = 'Valid = 1 AND Download_Land_Data > 0 AND SubStationStatus IS NOT NULL AND SubStationStatus = 3'

    return settings_dictionary

def get_current_timestamp():
    strDateFormat = '%Y%m%d'
    strNewTimeStamp = datetime.date.today().strftime(strDateFormat)
    hour = datetime.datetime.utcnow().strftime('%H')
    minute = datetime.datetime.utcnow().strftime('%M')

    strNewTimeStamp = strNewTimeStamp + "_" + hour + minute

    return strNewTimeStamp

def get_database_timestamp():

    strDateFormat = '%Y-%m-%d' #YYYY-MM-DD
    strNewTimeStamp = datetime.date.today().strftime(strDateFormat)
    strDateFormat = ' %H:%M:%S' #hh:mm:ss
    strNewTimeStamp = strNewTimeStamp + datetime.datetime.utcnow().strftime(strDateFormat)

    return strNewTimeStamp

def create_shapefile_and_kmz_for_valid_storage_polygons(settings_dictionary):

    select_required_polygons(settings_dictionary)

    if (selected_polygons_ok(settings_dictionary)):
        create_shapefile_and_zip(settings_dictionary)
        create_kmz(settings_dictionary)
        tidy_up(settings_dictionary, True)
    else:
        report_issue(settings_dictionary)
        tidy_up(settings_dictionary, False)

def select_required_polygons(settings_dictionary):
    arcpy.env.workspace = settings_dictionary["InputDatabase"]

    output_message("Selecting polygons...")
    arcpy.Select_analysis(settings_dictionary["InputFeatureClassViewPath"], settings_dictionary["outputFeatureClass"], settings_dictionary["ViewWhereClause"])
    output_message("... polygon selection complete")

def selected_polygons_ok(settings_dictionary):
    count = int(arcpy.GetCount_management(settings_dictionary["outputFeatureClass"]).getOutput(0))
    output_message("%s polygons selected" % (count))
    return (count > 0)

def create_shapefile_and_zip(settings_dictionary):

    create_folder_for_shapefile(settings_dictionary)
    add_centroids(settings_dictionary)
    create_mxd(settings_dictionary)
    export_shapefile(settings_dictionary)
    zip_shapefile(settings_dictionary)

def create_folder_for_shapefile(settings_dictionary):
    #create folder for shapefile
    if not os.path.exists(settings_dictionary["outputShapeFileFolder"]):
		output_warning('Creating {} directory'.format(settings_dictionary["outputShapeFileFolder"]))
		os.makedirs(settings_dictionary["outputShapeFileFolder"])

def add_centroids(settings_dictionary):

    #Add XY centrepoint as field
    output_message("Adding centroids...")
    inFeatures = settings_dictionary["outputFeatureClass"]
    fieldName1 = "xCentroid"
    fieldName2 = "yCentroid"

    fieldPrecision = 18
    fieldScale = 11
    expression1 = "1.5"
    expression2 = "2.5"

    # Execute AddField
    arcpy.AddField_management(inFeatures, fieldName1, "DOUBLE",
                              fieldPrecision, fieldScale)
    arcpy.AddField_management(inFeatures, fieldName2, "DOUBLE",
                              fieldPrecision, fieldScale)

    # Execute CalculateField
    arcpy.CalculateField_management(inFeatures, fieldName1, expression1,
                                    "PYTHON_9.3")
    output_message("Added X Centroid")

    arcpy.CalculateField_management(inFeatures, fieldName2, expression2,
                                    "PYTHON_9.3")
    output_message("Added Y Centroid")

def create_mxd(settings_dictionary):
    output_message("Creating mxd...")

    inFeatures = settings_dictionary["outputFeatureClass"]
    mxd = arcpy.mapping.MapDocument(settings_dictionary["TemplateMXD"])

    output_message('mxd opening from ' + mxd.filePath)

    arcpy.MakeFeatureLayer_management(inFeatures,"Boundary")
    df = arcpy.mapping.ListDataFrames(mxd)[0]
    output_message('List first dataframe from the mxd successful')

    lyrLayer = arcpy.mapping.Layer("Boundary")
    lyrFile = arcpy.mapping.Layer(settings_dictionary["styleLYR"])
    arcpy.mapping.AddLayer(df, lyrLayer, "AUTO_ARRANGE")
    updateLayer = arcpy.mapping.ListLayers(mxd, "Boundary", df)[0]
    arcpy.mapping.UpdateLayer(df, updateLayer, lyrFile, True)
    mxd.saveACopy(settings_dictionary["outputMXD"])
    del mxd

    msg = "Mxd copy Saved in: " + settings_dictionary["outputMXD"]
    output_message(msg)

    #use df.extents to zoom to the landregisrty feature before plotting to pdf.
    mxd =arcpy.mapping.MapDocument(settings_dictionary["outputMXD"])
    mxd.title = settings_dictionary["RunIdentifier"]
    cur = arcpy.UpdateCursor(lyrLayer)
    for row in cur:
        X = row.xCentroid
        X= round(X,0)
        Y = row.yCentroid
        Y = round(Y,0)
        mxd.summary = "Easting: %s, Northing %s" %(X,Y)

    df = arcpy.mapping.ListDataFrames(mxd)[0]
    lyrs = arcpy.mapping.ListLayers(mxd)[0]

    arcpy.SelectLayerByAttribute_management(lyrLayer,"NEW_SELECTION", "")
    df.extent = lyrLayer.getSelectedExtent(False)
    df.scale = df.scale *1.5
    arcpy.SelectLayerByAttribute_management(lyrLayer,"CLEAR_SELECTION", "")
    arcpy.ApplySymbologyFromLayer_management(lyrs, settings_dictionary["styleLYR"])
    arcpy.mapping.ExportToPDF(mxd,settings_dictionary["outputPDF"], "page_layout")
    mxd.save()
    del mxd
    output_message("mxd created")

def zip_shapefile(settings_dictionary):
    output_message("Zip shapefile...")
    zip = zipfile.ZipFile(settings_dictionary["outputShapeFileFolderZipped"], 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(settings_dictionary["outputShapeFileFolder"]) + 1
    for base, dirs, files in os.walk(settings_dictionary["outputShapeFileFolder"]):
        for file in files:
            if not file.endswith('.lock'):
                fn = os.path.join(base, file)
                zip.write(fn,fn[rootlen:])

    zip.close()
    output_message("Shapefile zipped")

def export_shapefile(settings_dictionary):
    output_message("Exporting shapefile...")
    arcpy.FeatureClassToShapefile_conversion(settings_dictionary["outputFeatureClass"], settings_dictionary["outputShapeFileFolder"])
    output_message("Shapefile exported")

def create_kmz(settings_dictionary):
    output_message("Creating KMZ...")
    arcpy.MakeFeatureLayer_management(settings_dictionary["outputFeatureClass"], settings_dictionary["temporaryLayer"])
    arcpy.LayerToKML_conversion(settings_dictionary["temporaryLayer"], settings_dictionary["outputKMZ"])
    output_message("KMZ created")

def report_issue(settings_dictionary):
    msg = 'ERROR: No polygons found in %s with query filter: %s' %(settings_dictionary["InputFeatureClassViewPath"], settings_dictionary["ViewWhereClause"])
    arcpy.AddError(msg)

def output_message(message):
    print message
    arcpy.AddMessage(message)

def output_warning(message):
	print message
	arcpy.AddWarning(message)

def tidy_up(settings_dictionary, ok):
    if (ok):
        shutil.rmtree(settings_dictionary["outputShapeFileFolder"])
    arcpy.Delete_management(settings_dictionary["outputFeatureClass"])
    del settings_dictionary["outputShapeFileFolder"]
    del settings_dictionary["outputShapeFile"]
    del settings_dictionary["outputFeatureClass"]
    del settings_dictionary["outputShapeFileFolderZipped"]
    del settings_dictionary["outputPDF"]
    del settings_dictionary["outputMXD"]
    del settings_dictionary["temporaryLayer"]
    del settings_dictionary["outputKMZ"]

if __name__ == '__main__':
    main()
