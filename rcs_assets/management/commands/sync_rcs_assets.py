from django.core.management.base import BaseCommand
from django.conf import settings
import json
import requests
from time import sleep
#from tracking import utils_freshdesk
#from tracking.utils import logger_setup
#from rcs_assets.models import FsComAssets, FsComManufacturerModels, FsComManufacturers
from rcs_assets.models import *
from assets.models import HardwareAsset, Vendor, HardwareModel, Suppliers, HardwareAssetExtra
from organisation.models import Location
import confy
from confy import env, database, cache
from django.core import serializers

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

class Command(BaseCommand):
    help = 'Sync RCS assets from the rcs asset system into OIM.'

    def handle(self, *args, **options):
		confy.read_environment_file()
		ErrorReportFromEmail = "asi@dpaw.wa.gov.au"
		ErrorReportEmail = "asi@dpaw.wa.gov.au"

		if env("ERROR_REPORTS_EMAIL"):
			ErrorReportEmail = env("ERROR_REPORTS_EMAIL")

		print "DEBUG Notification Email Address:"+ErrorReportEmail

#		ErrorReportEmail = 'jason.moore@dpaw.wa.gov.au'
		venList = {}
		assetTypeList = {}
		supList = {} 
		statusList = {} 
		assetModelList = {} 

		print "Creating Unknown ID fields for Supplier, Locations, Vendors"
		# Check For Default Data
		try:
			supCheck = Suppliers.objects.get(id=0)
		except Suppliers.DoesNotExist:
			Suppliers.objects.create(id=0, name='Unknown Supplier' )	

		try:
			locCheck = Location.objects.get(id=0)
		except Location.DoesNotExist:
			Location.objects.create(id=0, name='Unknown Location', address="Unknown Address" )

		try: 
			venCheck = Vendor.objects.get(id=0)
		except Vendor.DoesNotExist:
			Vendor.objects.create(id=0, name='Unknown Vendor')

		print "Creating and Validating Manufactures --> Vendors ";
		# Manufacturers are Vendor equivelent in OIM.
		allManU = FsComManufacturers.objects.all()
		for manu in allManU:
			# Check if Vendor exists in OIM ..  If does not exist create it.
		 	assetVen = None	
			try:
				assetVen = Vendor.objects.get(name=manu.name)
			except Vendor.DoesNotExist:
				assetVen = None
				venCreate = Vendor.objects.create()
				venCreate.name = manu.name
				venCreate.save()

		# Create temport vendor to manufacture map list.
		allManU = FsComManufacturers.objects.all()
		for manu in allManU:
			assetVen = Vendor.objects.get(name=manu.name)
			venList[manu.mnf_id] = assetVen.id



		MODEL_TYPE_CHOICES = dict(HardwareModel.TYPE_CHOICES)

		allAssetsTypes = FsComAssetTypes.objects.all()
		for AssetType in allAssetsTypes:
			# print AssetType.name
			assetTypeList[AssetType.att_id] = 'Comms - '+AssetType.name
#			print assetTypeList['Comms - '+AssetType.name]
			try:
				MODEL_TYPE_CHOICES['Comms - '+AssetType.name]
			except KeyError:
				fromaddr = ErrorReportFromEmail 
				toaddr = ErrorReportEmail
				msg = MIMEMultipart()
				msg['From'] = fromaddr
				msg['To'] = toaddr
				msg['Subject'] = "FC_COM Asset Import Hardware Model Choice Does not Exist"
				 
				body = "Hello,\n\nALERT:\n\nThe follow hardware model type choice does not exist in OIM Assets:\n\n -> "+AssetType.name+" \n\n Please update the assets.models.py file with the missing model category type.\n\nKind Regards\nOIM-ASI Robot"
				msg.attach(MIMEText(body, 'plain'))
				  
				server = smtplib.SMTP('localhost', 25)
				server.starttls()
				text = msg.as_string()
				server.sendmail(fromaddr, toaddr, text)
				server.quit()
	
		allManModels = FsComManufacturerModels.objects.all()
		for ManModels in allManModels:
			try:
				hwModel = HardwareModel.objects.get(model_no=ManModels.name)
			except HardwareModel.DoesNotExist:			
				print "Model doesn't exist, Trying to Create it: "+ManModels.name
				hwModelCreate = HardwareModel.objects.create(lifecycle=5, vendor_id=venList[ManModels.mnf_id], model_no=ManModels.name, model_type=assetTypeList[ManModels.att_id])


		# Get Model to OIM link Id
		allManModels = FsComManufacturerModels.objects.all()
		for ManModels in allManModels:
			hwModel = HardwareModel.objects.get(model_no=ManModels.name)
			assetModelList[ManModels.mod_id] = hwModel.id
		

		# Suppliers
		print "Creating and Validating Suppliers"
		allSuppliers = FsComSuppliers.objects.all()
		for sup in allSuppliers:

			try:
				sipRow = Suppliers.objects.get(name=sup.name)	
			except Suppliers.DoesNotExist:
				supCreate = Suppliers.objects.create(name=sup.name,address1=sup.address_line_1, address2=sup.address_line_2, address3=sup.address_line_3, suburb=sup.town_suburb,postcode=sup.postcode,state=sup.state, effective_from=sup.effective_from,effective_to=sup.effective_to)

		# Create Supplier ID match list with FS_COM and OIM
		allSuppliers = FsComSuppliers.objects.all()
		supList[0] = '0'
		for sup in allSuppliers:
			sipRow = Suppliers.objects.get(name=sup.name)
			supList[sup.sup_id] = sipRow.id




		print "Preparing to create FS_COM assets in OIM"
		allFsComAssets = FsComAssets.objects.all()
		for fscomasset in allFsComAssets:
			if fscomasset.sup_id is None:
				fscomasset.sup_id = 0
			ManModels = FsComManufacturerModels.objects.get(mod_id=fscomasset.mod_id)
#			print "MAN MODEL"
#			print ManModels.mnf_id
#			print "===---=========="
#
#			print "---==== NEW RECORD ====---";
#			print fscomasset.ast_id
#			print fscomasset.sup_id
#			print fscomasset.mod_id
#			print fscomasset.dec_serial_no
#			print fscomasset.manufacturer_serial_no
#			print fscomasset.dec_comms_purchase
#			print fscomasset.purchase_price_ex_gst
#			print fscomasset.purchase_order_no
#			print fscomasset.purchase_date
#			print fscomasset.warranty_expiry_date
#			print fscomasset.dec_asset_no
#			print fscomasset.dec_asset_label_attached
#			print fscomasset.denorm_asy.name
#			print fscomasset.comments
#			print fscomasset.date_modified
#			print fscomasset.modified_by
#			print fscomasset.date_created
#			print fscomasset.created_by
#			print "============================";

			#print fscomasset.extra_data
			if fscomasset.dec_asset_no is None: 
				fscomasset.dec_asset_no = "NOTAG"+str(fscomasset.ast_id)
			#print "Working"
			assetexists = 'no'
			try:
				getAssetInfo  = HardwareAsset.objects.get(rsid=fscomasset.ast_id)
#				print "--====RSID Exsits===--"
#				print getAssetInfo.id
				assetexists = 'yes'
				getAssetInfo.date_created = fscomasset.date_created
				getAssetInfo.date_updated = fscomasset.date_modified
				getAssetInfo.date_purchased = fscomasset.purchase_date
				getAssetInfo.purchased_value = fscomasset.purchase_price_ex_gst
				getAssetInfo.asset_tag = fscomasset.dec_asset_no
				getAssetInfo.finance_asset_tag = fscomasset.dec_serial_no
				getAssetInfo.status = fscomasset.denorm_asy.name
				getAssetInfo.serial = fscomasset.manufacturer_serial_no
				getAssetInfo.hardware_model_id = assetModelList[fscomasset.mod_id]
				getAssetInfo.invoice_id = None
				getAssetInfo.location_id = 0
				getAssetInfo.org_unit_id = 1
				getAssetInfo.vendor_id = venList[ManModels.mnf_id]
				getAssetInfo.supplier_id = supList[fscomasset.sup_id]
				getAssetInfo.notes = fscomasset.comments
				getAssetInfo.rsid = fscomasset.ast_id
#				rowjsondata = serializers.serialize("json", fscomasset)
#				getAssetInfo.extra_data = rowjsondata
#				print toJSON(fscomasset)
				try: 
					rowjsondata = serializers.serialize("json", [fscomasset,])
					getAssetInfo.extra_data = rowjsondata
					getAssetInfo.save()
					print "Updated FC_COM --> OIM record: "+str(fscomasset.ast_id)
#					print "===-=-=-=-= UPDATING RECORD ===-=-=-="
				except Exception, d:
					print "Update Exception sent to: " + ErrorReportEmail
					fromaddr = "asi@dpaw.wa.gov.au"
					toaddr = ErrorReportEmail
					msg = MIMEMultipart()
					msg['From'] = fromaddr
					msg['To'] = toaddr
					msg['Subject'] = "UPDATE ASSET: Error Importing Asset Record"
					
					body = "Hello,\n\nThere was and error importing and asset into OIM.  See information below:\n\n[Exception]\n"+str(d)+" \n[Object]"
					body += "\ndate_created: "+str(fscomasset.date_created)
					body += "\ndate_updated: "+str(fscomasset.date_modified)
					body += "\ndate_purchased: "+str(fscomasset.purchase_date)
					body += "\npurchased_value: "+str(fscomasset.purchase_price_ex_gst)
					body += "\nasset_tag: "+str(fscomasset.dec_asset_no)
					body += "\nfinance_asset_tag: "+str(fscomasset.dec_serial_no)
					body += "\nstatus: "+ str(fscomasset.denorm_asy.name)
					body += "\nserial: "+ str(fscomasset.manufacturer_serial_no)
					body += "\nhardware_model_id: "+str(assetModelList[fscomasset.mod_id])
					body += "\ninvoice_id: None"
					body += "\nlocation_id: 0"
					body += "\norg_unit_id: 1"
					body += "\nvendor_id: "+ str(venList[ManModels.mnf_id])
					body += "\nsupplier_id: "+str(supList[fscomasset.sup_id])
					body += "\nnotes: "+fscomasset.comments
					body += "\nrsid: "+str(fscomasset.ast_id)
					body += "\n"
					body += "\nKind Regards\nOIM-ASI Robot"
					msg.attach(MIMEText(body, 'plain'))
	
					server = smtplib.SMTP('localhost', 25)
					server.starttls()
					# server.login(fromaddr, "")
					text = msg.as_string()
					server.sendmail(fromaddr, toaddr, text)
					server.quit()
			except Exception, e:
				assetexists = 'no'
				# print "exists"
				# print e


			if assetexists is 'no':
				try: 

					rowjsondata = serializers.serialize("json", [fscomasset,])

					HWA = HardwareAsset.objects.create(
						date_created = fscomasset.date_created,
						date_updated = fscomasset.date_modified,
						date_purchased = fscomasset.purchase_date,
						purchased_value = fscomasset.purchase_price_ex_gst,
						asset_tag = fscomasset.dec_asset_no,
						finance_asset_tag = fscomasset.dec_serial_no,
						status = fscomasset.denorm_asy.name,
						serial = fscomasset.manufacturer_serial_no,
						hardware_model_id = assetModelList[fscomasset.mod_id],
						invoice_id = None,
						location_id = 0,
						org_unit_id = 1,
						vendor_id = venList[ManModels.mnf_id],
						supplier_id = supList[fscomasset.sup_id],
						notes = fscomasset.comments,
						rsid = fscomasset.ast_id,
						extra_data = rowjsondata
					)
					print "New Asset From FC_COM record: "+str(fscomasset.ast_id)

				except Exception, e:
					print "New Asset Exception sent to: " + ErrorReportEmail
					fromaddr = "asi@dpaw.wa.gov.au"
					toaddr = ErrorReportEmail
					msg = MIMEMultipart()
					msg['From'] = fromaddr
					msg['To'] = toaddr
					msg['Subject'] = "NEW ASSET: Error Importing Asset Record"

					body = "Hello,\n\nThere was and error importing and asset into OIM.  See information below:\n\n[Exception]\n"+str(e)+" \n[Object]"
					body += "\ndate_created: "+str(fscomasset.date_created)
					body += "\ndate_updated: "+str(fscomasset.date_modified)
					body += "\ndate_purchased: "+str(fscomasset.purchase_date)
					body += "\npurchased_value: "+str(fscomasset.purchase_price_ex_gst)
					body += "\nasset_tag: "+str(fscomasset.dec_asset_no)
					body += "\nfinance_asset_tag: "+str(fscomasset.dec_serial_no)
					body += "\nstatus: "+ str(fscomasset.denorm_asy.name)
					body += "\nserial: "+ str(fscomasset.manufacturer_serial_no)
					body += "\nhardware_model_id: "+str(assetModelList[fscomasset.mod_id])
					body += "\ninvoice_id: None"
					body += "\nlocation_id: 0"
					body += "\norg_unit_id: 1"
					body += "\nvendor_id: "+ str(venList[ManModels.mnf_id])
					body += "\nsupplier_id: "+str(supList[fscomasset.sup_id])
					body += "\nnotes: "+fscomasset.comments
					body += "\nrsid: "+str(fscomasset.ast_id)
					body += "\n"
					body += "\nKind Regards\nOIM-ASI Robot"
					msg.attach(MIMEText(body, 'plain'))

					server = smtplib.SMTP('localhost', 25)
					server.starttls()
                	# server.login(fromaddr, "")
					text = msg.as_string()
					server.sendmail(fromaddr, toaddr, text)
					server.quit()



		# Hardware Assets Extras
		hweAll = HardwareAsset.objects.filter(rsid__gte=0)
		for hwe in hweAll:

			# GET 2WAYSATS
			try:
				ComSat = FsComAsset2WaySats.objects.get(ast_id=hwe.rsid)
				print ComSat.sat_id
				print "ASSET"
				print hwe.id
				print ComSat.service_provider
				print ComSat.service_plan
				try:
					oimAssetExtra = HardwareAssetExtra.objects.get(ha_id=hwe.id)
					oimAssetExtra.comms_type = ComSat.sat_type
					oimAssetExtra.service_provider = ComSat.service_provider
					oimAssetExtra.service_plan = ComSat.service_plan
					oimAssetExtra.save()
				except HardwareAssetExtra.DoesNotExist:
					HardwareAssetExtra.objects.create(ha_id = hwe.id,
							comms_type = ComSat.sat_type
							)
					#                   itdoesnot = "DOES NOT EXIST"
#               HardwareAsset.objects.get(id=hwe.id)
			except FsComAsset2WaySats.DoesNotExist:
				itdoesnot = "DOES NOT EXIST"

			#SimInfo = FsComAssetSimCards.objects.get(ast_id=hwe.rsid)
			# GET SIM INFO
			try:
				SimInfo = FsComAssetSimCards.objects.get(ast_id=hwe.rsid)
				print SimInfo.voice_no
				print SimInfo.fax_no
				print SimInfo.msisdn
				print SimInfo.service_provider
				print SimInfo.service_plan
				print SimInfo.sim_pin
				print SimInfo.account_number
				try:
					oimAssetExtra = HardwareAssetExtra.objects.get(ha_id=hwe.id)
					oimAssetExtra.comms_type = 'SIM'
					oimAssetExtra.service_provider = SimInfo.service_provider
					oimAssetExtra.service_plan = SimInfo.service_plan
					oimAssetExtra.voice_no = SimInfo.voice_no
					oimAssetExtra.fax_no = SimInfo.fax_no
					oimAssetExtra.icc_id = SimInfo.icc_id
					oimAssetExtra.msisdn = SimInfo.msisdn
					oimAssetExtra.account_number = SimInfo.account_number
					oimAssetExtra.sim_pin = SimInfo.sim_pin
					oimAssetExtra.account_pin = SimInfo.account_pin
					oimAssetExtra.date_modified = SimInfo.date_modified
					oimAssetExtra.date_created = SimInfo.date_created
					oimAssetExtra.save()
				except:
					HardwareAssetExtra.objects.create(ha_id = hwe.id,
								comms_type = 'SIM',
								service_provider = SimInfo.service_provider,
								service_plan = SimInfo.service_plan,
								voice_no = SimInfo.voice_no,
								fax_no = SimInfo.fax_no,
								icc_id = SimInfo.icc_id,
								msisdn = SimInfo.msisdn,
								account_number = SimInfo.account_number,
								account_pin = SimInfo.account_pin,
								sim_pin = SimInfo.sim_pin,
								date_modified = SimInfo.date_modified,
								date_created = SimInfo.date_created
						)

			except FsComAssetSimCards.DoesNotExist:
				print "DOSE NOT EXIST"

            # GET Asset VEHC DRIVERS
			try:
				VehcTrackInfo = FsComAssetVehcTrackDevs.objects.get(ast_id=hwe.rsid)
				try:
					print VehcTrackInfo.vtd_id
					oimAssetExtra = HardwareAssetExtra.objects.get(ha_id=hwe.id)
					oimAssetExtra.comms_type = 'VEHC'
					oimAssetExtra.service_provider = VehcTrackInfo.service_provider
					oimAssetExtra.service_plan = VehcTrackInfo.service_plan
					oimAssetExtra.sim_pin = VehcTrackInfo.sim_pin
					oimAssetExtra.account_number = VehcTrackInfo.account_number
					oimAssetExtra.account_pin = VehcTrackInfo.account_pin
					oimAssetExtra.date_modified = VehcTrackInfo.date_modified
					oimAssetExtra.date_created = VehcTrackInfo.date_created
					oimAssetExtra.save()
				except:
					HardwareAssetExtra.objects.create(ha_id = hwe.id,
							comms_type = 'VEHC',
							service_provider = VehcTrackInfo.service_provider,
							service_plan = VehcTrackInfo.service_plan,
							sim_pin = VehcTrackInfo.sim_pin,
							account_number = VehcTrackInfo.account_number,
							account_pin = VehcTrackInfo.account_pin,
							date_modified = VehcTrackInfo.date_modified,
							date_created = VehcTrackInfo.date_created
						)
					print "Creating"
					print hwe.id
			except FsComAssetVehcTrackDevs.DoesNotExist:
				print "VEHC DOSE NOT EXIST"
                                                                        



