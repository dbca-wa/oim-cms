# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals
from django.db import models


class FsApplications(models.Model):
    fap_id = models.CharField(primary_key=True, max_length=10)
    app_code = models.CharField(max_length=10)
    name = models.CharField(unique=True, max_length=50)
    created_by = models.CharField(max_length=30)
    created_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'fs_applications'


class FsComAgencies(models.Model):
    cag_id = models.IntegerField(primary_key=True)
    agency_abrv = models.CharField(unique=True, max_length=3)
    agency_name = models.CharField(unique=True, max_length=40)
    agency_loading = models.DecimalField(max_digits=5, decimal_places=2)
    agency_bill_adjustment = models.DecimalField(max_digits=5, decimal_places=2)
    created_by = models.CharField(max_length=30)
    date_created = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_modified = models.DateField()

    class Meta:
        managed = False
        db_table = 'fs_com_agencies'

class FsComAsset2WaySats(models.Model):
    sat_id = models.IntegerField(primary_key=True)
    ast = models.OneToOneField('FsComAssets', models.DO_NOTHING)
    sat_type = models.CharField(max_length=15)
    lnb_manufacturer_serial_no = models.CharField(max_length=50, blank=True, null=True)
    buc_manufacturer_serial_no = models.CharField(max_length=50, blank=True, null=True)
    dish_manufacturer_serial_no = models.CharField(max_length=50, blank=True, null=True)
    service_provider = models.CharField(max_length=50, blank=True, null=True)
    service_plan = models.CharField(max_length=50, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_pin = models.IntegerField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_2way_sats'


class FsComAssetBgans(models.Model):
    bgn_id = models.IntegerField(primary_key=True)
    ast = models.OneToOneField('FsComAssets', models.DO_NOTHING)
    part_no = models.CharField(max_length=50, blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_bgans'


class FsComAssetConfigTypes(models.Model):
    act_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_config_types'
        unique_together = (('name', 'effective_from'),)


class FsComAssetHireRates(models.Model):
    ahr_id = models.IntegerField(primary_key=True)
    mmc = models.ForeignKey('FsComManuModelConfigTypes', models.DO_NOTHING)
    annual_rate = models.DecimalField(max_digits=8, decimal_places=2)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    created_by = models.CharField(max_length=30)
    date_created = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_modified = models.DateField()

    class Meta:
        managed = False
        db_table = 'fs_com_asset_hire_rates'


class FsComAssetHires(models.Model):
    ash_id = models.IntegerField(primary_key=True)
    ast = models.ForeignKey('FsComAssets', models.DO_NOTHING)
    cst = models.ForeignKey('FsCostCentres', models.DO_NOTHING, blank=True, null=True)
    nda = models.ForeignKey('FsComNonDecAgencies', models.DO_NOTHING, blank=True, null=True)
    swap_ash = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    charge_pct = models.IntegerField()
    deployable = models.CharField(max_length=1)
    comments = models.CharField(max_length=500, blank=True, null=True)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    expected_return_date = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)
    mmc = models.ForeignKey('FsComManuModelConfigTypes', models.DO_NOTHING, blank=True, null=True)
    cst_id_physical = models.ForeignKey('FsCostCentres', models.DO_NOTHING, db_column='cst_id_physical', blank=True, null=True, related_name='cst_id_physical')

    class Meta:
        managed = False
        db_table = 'fs_com_asset_hires'
        unique_together = (('ast', 'cst', 'nda', 'effective_from', 'effective_to'),)


class FsComAssetLocationTypes(models.Model):
    lct_id = models.IntegerField(primary_key=True)
    code = models.CharField(unique=True, max_length=4)
    name = models.CharField(max_length=50)
    fixed_location_install = models.CharField(max_length=1)
    type_flag = models.CharField(max_length=15)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_location_types'
        unique_together = (('name', 'effective_from'),)


class FsComAssetLocations(models.Model):
    loc_id = models.IntegerField(primary_key=True)
    ast = models.ForeignKey('FsComAssets', models.DO_NOTHING)
    lct = models.ForeignKey('FsComAssetLocationTypes', models.DO_NOTHING)
    reg = models.ForeignKey('FsRegions', models.DO_NOTHING, blank=True, null=True)
    dis = models.ForeignKey('FsDistricts', models.DO_NOTHING, blank=True, null=True)
    sit = models.ForeignKey('FsSites', models.DO_NOTHING, blank=True, null=True)
    building_name = models.CharField(max_length=100, blank=True, null=True)
    building_addr_line1 = models.CharField(max_length=200, blank=True, null=True)
    building_addr_line2 = models.CharField(max_length=200, blank=True, null=True)
    building_addr_line3 = models.CharField(max_length=200, blank=True, null=True)
    building_postcode = models.IntegerField(blank=True, null=True)
    building_state = models.CharField(max_length=3, blank=True, null=True)
    vehicle_id = models.IntegerField(blank=True, null=True)
    dec_emp_no = models.ForeignKey('FsResPeople', models.DO_NOTHING, db_column='dec_emp_no', blank=True, null=True)
    dec_contact_emp_no = models.ForeignKey('FsResPeople', models.DO_NOTHING, db_column='dec_contact_emp_no', blank=True, null=True, related_name='dec_contact_emp_no')
    non_dec_emp_first_name = models.CharField(max_length=100, blank=True, null=True)
    non_dec_emp_surname = models.CharField(max_length=100, blank=True, null=True)
    non_dec_emp_organisation = models.CharField(max_length=100, blank=True, null=True)
    non_dec_emp_contact_no = models.CharField(max_length=10, blank=True, null=True)
    non_dec_emp_email = models.CharField(max_length=100, blank=True, null=True)
    non_dec_contact_details = models.CharField(max_length=500, blank=True, null=True)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    comments = models.CharField(max_length=500, blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_locations'


class FsComAssetRadios(models.Model):
    rad_id = models.IntegerField(primary_key=True)
    ast = models.OneToOneField('FsComAssets', models.DO_NOTHING)
    uhf_dec_serial_no = models.CharField(max_length=9, blank=True, null=True)
    uhf_manufacturer_serial_no = models.CharField(max_length=50, blank=True, null=True)
    hi_band_dec_serial_no = models.CharField(max_length=9, blank=True, null=True)
    hi_band_manufacturer_serial_no = models.CharField(max_length=50, blank=True, null=True)
    selcall_number = models.BigIntegerField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_radios'


class FsComAssetSatPhones(models.Model):
    sph_id = models.IntegerField(primary_key=True)
    ast = models.OneToOneField('FsComAssets', models.DO_NOTHING)
    sph_type = models.CharField(max_length=15)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_sat_phones'


class FsComAssetSimCards(models.Model):
    sim_id = models.IntegerField(primary_key=True)
    ast = models.OneToOneField('FsComAssets', models.DO_NOTHING)
    voice_no = models.CharField(max_length=20)
    fax_no = models.CharField(max_length=20, blank=True, null=True)
    icc_id = models.CharField(max_length=20)
    msisdn = models.CharField(max_length=12)
    service_provider = models.CharField(max_length=50, blank=True, null=True)
    service_plan = models.CharField(max_length=50, blank=True, null=True)
    sim_pin = models.IntegerField(blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_pin = models.IntegerField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_sim_cards'


class FsComAssetStatus(models.Model):
    ata_id = models.IntegerField(primary_key=True)
    ast = models.ForeignKey('FsComAssets', models.DO_NOTHING)
    asy = models.ForeignKey('FsComAssetStatusTypes', models.DO_NOTHING)
    ash = models.ForeignKey('FsComAssetHires', models.DO_NOTHING, blank=True, null=True)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_status'
        unique_together = (('ast', 'asy', 'effective_from'),)


class FsComAssetStatusTypes(models.Model):
    asy_id = models.IntegerField(primary_key=True)
    code = models.CharField(unique=True, max_length=4)
    name = models.CharField(max_length=40)
    on_create_asset = models.CharField(max_length=1)
    on_edit_asset = models.CharField(max_length=1)
    on_return_asset = models.CharField(max_length=1)
    on_write_off_asset = models.CharField(max_length=1)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_status_types'
        unique_together = (('name', 'effective_from'),)


class FsComAssetTypes(models.Model):
    att_id = models.IntegerField(primary_key=True)
    code = models.CharField(unique=True, max_length=4)
    name = models.CharField(max_length=50)
    generic_asset = models.CharField(max_length=1)
    charge_splitable = models.CharField(max_length=1)
    apex_edit_page_number = models.IntegerField()
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_types'
        unique_together = (('name', 'effective_from'),)


class FsComAssetVehcTrackDevs(models.Model):
    vtd_id = models.IntegerField(primary_key=True)
    ast = models.OneToOneField('FsComAssets', models.DO_NOTHING)
    service_provider = models.CharField(max_length=50, blank=True, null=True)
    service_plan = models.CharField(max_length=50, blank=True, null=True)
    sim_pin = models.IntegerField(blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_pin = models.IntegerField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_asset_vehc_track_devs'


class FsComAssets(models.Model):
    ast_id = models.IntegerField(primary_key=True)
    sup = models.ForeignKey('FsComSuppliers', models.DO_NOTHING, blank=True, null=True)
    mod = models.ForeignKey('FsComManufacturerModels', models.DO_NOTHING)
    dec_serial_no = models.CharField(unique=True, max_length=12)
    manufacturer_serial_no = models.CharField(max_length=50, blank=True, null=True)
    dec_comms_purchase = models.CharField(max_length=1)
    purchase_price_ex_gst = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    purchase_order_no = models.CharField(max_length=20, blank=True, null=True)
    purchase_date = models.DateField()
    warranty_expiry_date = models.DateField(blank=True, null=True)
    dec_asset_no = models.IntegerField(blank=True, null=True)
    dec_asset_label_attached = models.CharField(max_length=1)
    denorm_asy = models.ForeignKey('FsComAssetStatusTypes', models.DO_NOTHING, blank=True, null=True)
    comments = models.CharField(max_length=500, blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_assets'


class FsComDecSerialCodes(models.Model):
    dsc_id = models.IntegerField(primary_key=True)
    parent_dsc = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    dec_serial_code = models.CharField(unique=True, max_length=7)
    next_dec_serial_no = models.IntegerField(blank=True, null=True)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_dec_serial_codes'


class FsComFlexfields(models.Model):
    flx_id = models.IntegerField(primary_key=True)
    cst = models.ForeignKey('FsCostCentres', models.DO_NOTHING)
    flexfield_code = models.CharField(max_length=30)
    percentage_split = models.DecimalField(max_digits=5, decimal_places=2)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    created_by = models.CharField(max_length=30)
    date_created = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_modified = models.DateField()

    class Meta:
        managed = False
        db_table = 'fs_com_flexfields'


class FsComManuModelConfigTypes(models.Model):
    mmc_id = models.IntegerField(primary_key=True)
    act = models.ForeignKey('FsComAssetConfigTypes', models.DO_NOTHING)
    mod = models.ForeignKey('FsComManufacturerModels', models.DO_NOTHING)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_manu_model_config_types'
        unique_together = (('act', 'mod'),)


class FsComManufacturerModels(models.Model):
    mod_id = models.IntegerField(primary_key=True)
    mnf = models.ForeignKey('FsComManufacturers', models.DO_NOTHING)
    att = models.ForeignKey('FsComAssetTypes', models.DO_NOTHING)
    name = models.CharField(max_length=50)
    dsc = models.ForeignKey('FsComDecSerialCodes', models.DO_NOTHING)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_manufacturer_models'
        unique_together = (('mnf', 'att', 'name', 'dsc', 'effective_from'),)


class FsComManufacturers(models.Model):
    mnf_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_manufacturers'
        unique_together = (('name', 'effective_from'),)


class FsComNonDecAgencies(models.Model):
    nda_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    cst_id_required = models.CharField(max_length=1)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_non_dec_agencies'
        unique_together = (('name', 'effective_from'),)


class FsComSuppliers(models.Model):
    sup_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    address_line_1 = models.CharField(max_length=100, blank=True, null=True)
    address_line_2 = models.CharField(max_length=100, blank=True, null=True)
    address_line_3 = models.CharField(max_length=100, blank=True, null=True)
    town_suburb = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.IntegerField(blank=True, null=True)
    state = models.CharField(max_length=3, blank=True, null=True)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_suppliers'
        unique_together = (('name', 'effective_from'),)


class FsComWriteOffAssets(models.Model):
    woa_id = models.IntegerField(primary_key=True)
    wof = models.ForeignKey('FsComWriteOffs', models.DO_NOTHING)
    ast = models.ForeignKey('FsComAssets', models.DO_NOTHING)
    write_off_type_asy_id = models.IntegerField()
    written_down_value_ex_gst = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    effective_from = models.DateField()
    comments = models.CharField(max_length=500, blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_write_off_assets'
        unique_together = (('wof', 'ast'),)


class FsComWriteOffs(models.Model):
    wof_id = models.IntegerField(primary_key=True)
    requesting_dec_emp_no = models.ForeignKey('FsResPeople', models.DO_NOTHING, db_column='requesting_dec_emp_no')
    write_off_dec_emp_no = models.ForeignKey('FsResPeople', models.DO_NOTHING, db_column='write_off_dec_emp_no', related_name='write_off_dec_emp_no')
    effective_from = models.DateField()
    police_report_no = models.CharField(max_length=20, blank=True, null=True)
    comments = models.CharField(max_length=500, blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_com_write_offs'


class FsContactManagerMv(models.Model):
    id = models.BigIntegerField(primary_key=True)
    contact_type = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    salutation = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    surname = models.CharField(max_length=100, blank=True, null=True)
    org_name = models.CharField(max_length=100, blank=True, null=True)
    org_abbrev = models.CharField(max_length=50, blank=True, null=True)
    other_name = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=500, blank=True, null=True)
    job_function = models.CharField(max_length=500, blank=True, null=True)
    address = models.CharField(max_length=1000, blank=True, null=True)
    work_phone = models.CharField(max_length=50, blank=True, null=True)
    home_phone = models.CharField(max_length=50, blank=True, null=True)
    other_phone = models.CharField(max_length=50, blank=True, null=True)
    mobile_phone = models.CharField(max_length=50, blank=True, null=True)
    work_fax = models.CharField(max_length=50, blank=True, null=True)
    other_fax = models.CharField(max_length=50, blank=True, null=True)
    work_email = models.CharField(max_length=100, blank=True, null=True)
    other_email = models.CharField(max_length=100, blank=True, null=True)
    org_structure = models.BigIntegerField(blank=True, null=True)
    org_structure_auto = models.BigIntegerField(blank=True, null=True)
    org_structure_manual = models.BigIntegerField(blank=True, null=True)
    org_code = models.CharField(max_length=50, blank=True, null=True)
    site = models.BigIntegerField(blank=True, null=True)
    desk_location = models.CharField(max_length=100, blank=True, null=True)
    nt_login = models.CharField(max_length=50, blank=True, null=True)
    emp_code = models.CharField(max_length=20, blank=True, null=True)
    internet_enabled = models.CharField(max_length=1, blank=True, null=True)
    misc_comment = models.CharField(max_length=1000, blank=True, null=True)
    change_user = models.CharField(max_length=20)
    change_date = models.DateField()
    emp_code_old = models.CharField(max_length=50, blank=True, null=True)
    alias_name_old = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_contact_manager_mv'


class FsConv2WaySatDish(models.Model):
    id = models.FloatField(primary_key=True)
    supplier = models.CharField(max_length=30, blank=True, null=True)
    manufacturer = models.CharField(max_length=30, blank=True, null=True)
    model = models.CharField(max_length=30, blank=True, null=True)
    dec_serial = models.CharField(max_length=30, blank=True, null=True)
    manufacturer_serial = models.CharField(max_length=30, blank=True, null=True)
    purchased_by_dec_comms = models.CharField(max_length=10, blank=True, null=True)
    purchase_order = models.CharField(max_length=30, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry_date = models.DateField(blank=True, null=True)
    purchase_price = models.FloatField(blank=True, null=True)
    dec_asset = models.CharField(max_length=6, blank=True, null=True)
    status = models.CharField(max_length=1, blank=True, null=True)
    comments = models.CharField(max_length=1000, blank=True, null=True)
    type_fixedmobile = models.CharField(max_length=30, blank=True, null=True)
    lnb_serial_no = models.CharField(max_length=50, blank=True, null=True)
    buc_serial_no = models.CharField(max_length=50, blank=True, null=True)
    dish_serial_no = models.CharField(max_length=50, blank=True, null=True)
    modem_serial_no = models.CharField(max_length=50, blank=True, null=True)
    modem_model = models.CharField(max_length=50, blank=True, null=True)
    service_provider = models.CharField(max_length=50, blank=True, null=True)
    service_plan = models.CharField(max_length=50, blank=True, null=True)
    account_no = models.CharField(max_length=50, blank=True, null=True)
    account_password = models.CharField(max_length=50, blank=True, null=True)
    agency_fpcdec = models.CharField(max_length=3, blank=True, null=True)
    cost_centre = models.CharField(max_length=10, blank=True, null=True)
    chargeable_yesno = models.CharField(max_length=3, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_conv_2way_sat_dish'


class FsConv2WaySatSim(models.Model):
    id = models.FloatField(primary_key=True)
    supplier = models.CharField(max_length=30, blank=True, null=True)
    manufacturer = models.CharField(max_length=30, blank=True, null=True)
    model = models.CharField(max_length=30, blank=True, null=True)
    dec_serial = models.CharField(max_length=30, blank=True, null=True)
    manufacturer_serial = models.CharField(max_length=30, blank=True, null=True)
    purchased_by_dec_comms = models.CharField(max_length=10, blank=True, null=True)
    purchase_order = models.CharField(max_length=30, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry_date = models.DateField(blank=True, null=True)
    purchase_price = models.FloatField(blank=True, null=True)
    dec_asset = models.CharField(max_length=6, blank=True, null=True)
    status = models.CharField(max_length=1, blank=True, null=True)
    comments = models.CharField(max_length=1, blank=True, null=True)
    voice_number = models.CharField(max_length=10, blank=True, null=True)
    faxdata_number = models.CharField(max_length=10, blank=True, null=True)
    sim_icc_id = models.CharField(max_length=10, blank=True, null=True)
    msisdn = models.CharField(max_length=10, blank=True, null=True)
    service_provider = models.CharField(max_length=50, blank=True, null=True)
    service_plan = models.CharField(max_length=50, blank=True, null=True)
    pin_number = models.CharField(max_length=50, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_pin = models.CharField(max_length=50, blank=True, null=True)
    user_surname = models.CharField(max_length=50, blank=True, null=True)
    user_first_name = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=50, blank=True, null=True)
    agency_fpcdec = models.CharField(max_length=50, blank=True, null=True)
    cost_centre = models.CharField(max_length=50, blank=True, null=True)
    chargeable_yesno = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_conv_2way_sat_sim'


class FsConvRadio(models.Model):
    id = models.FloatField(primary_key=True)
    updated = models.CharField(max_length=30, blank=True, null=True)
    decorfpc = models.CharField(max_length=50, blank=True, null=True)
    costcentrenumber = models.CharField(max_length=30, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    dec_number = models.CharField(max_length=30, blank=True, null=True)
    manufactureserialnumber = models.CharField(max_length=30, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    other_information = models.CharField(max_length=500, blank=True, null=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    annual_rate = models.CharField(max_length=30, blank=True, null=True)
    unit_description = models.CharField(max_length=30, blank=True, null=True)
    purchasedate = models.CharField(max_length=30, blank=True, null=True)
    type = models.CharField(max_length=30, blank=True, null=True)
    assetnumber = models.CharField(max_length=30, blank=True, null=True)
    asset_labelattached = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_conv_radio'


class FsConvRadioTypeToManuf(models.Model):
    id = models.FloatField(primary_key=True)
    type = models.CharField(max_length=30, blank=True, null=True)
    unit_description = models.CharField(max_length=30, blank=True, null=True)
    asset_type = models.CharField(max_length=30, blank=True, null=True)
    manufacturer = models.CharField(max_length=30, blank=True, null=True)
    model = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_conv_radio_type_to_manuf'


class FsConvSatDish(models.Model):
    id = models.FloatField(primary_key=True)
    supplier = models.CharField(max_length=30, blank=True, null=True)
    manufacturer = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True)
    dec_serial = models.CharField(max_length=10, blank=True, null=True)
    manufacturer_serial = models.CharField(max_length=50, blank=True, null=True)
    purchased_by_dec_comms = models.CharField(max_length=10, blank=True, null=True)
    purchase_order = models.CharField(max_length=20, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry_date = models.DateField(blank=True, null=True)
    purchase_price = models.FloatField(blank=True, null=True)
    dec_asset = models.CharField(max_length=6, blank=True, null=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    comments = models.CharField(max_length=1000, blank=True, null=True)
    type_bganrbgan = models.CharField(max_length=30, blank=True, null=True)
    part = models.CharField(max_length=50, blank=True, null=True)
    user_surname = models.CharField(max_length=50, blank=True, null=True)
    user_first_name = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    agency_fpcdec = models.CharField(max_length=3, blank=True, null=True)
    cost_centre = models.CharField(max_length=10, blank=True, null=True)
    chargeable_yesno = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_conv_sat_dish'


class FsConvSatPhone(models.Model):
    id = models.FloatField(primary_key=True)
    supplier = models.CharField(max_length=30, blank=True, null=True)
    manufacturer = models.CharField(max_length=30, blank=True, null=True)
    model = models.CharField(max_length=30, blank=True, null=True)
    dec_serial = models.CharField(max_length=10, blank=True, null=True)
    manufacturer_serial = models.CharField(max_length=50, blank=True, null=True)
    purchased_by_dec_comms = models.CharField(max_length=10, blank=True, null=True)
    purchase_order = models.CharField(max_length=30, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry_date = models.DateField(blank=True, null=True)
    purchase_price = models.FloatField(blank=True, null=True)
    dec_asset = models.CharField(max_length=6, blank=True, null=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    comments = models.CharField(max_length=1000, blank=True, null=True)
    type_fixedmobile = models.CharField(max_length=30, blank=True, null=True)
    user_surname = models.CharField(max_length=50, blank=True, null=True)
    user_first_name = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    agency_fpcdec = models.CharField(max_length=3, blank=True, null=True)
    cost_centre = models.CharField(max_length=10, blank=True, null=True)
    chargeable_yesno = models.CharField(max_length=3, blank=True, null=True)
    other_information = models.CharField(max_length=30, blank=True, null=True)
    registration = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_conv_sat_phone'


class FsConvSatPhoneSim(models.Model):
    id = models.FloatField(primary_key=True)
    supplier = models.CharField(max_length=30, blank=True, null=True)
    manufacturer = models.CharField(max_length=50, blank=True, null=True)
    dec_serial = models.CharField(max_length=10, blank=True, null=True)
    manufacturer_serial = models.CharField(max_length=50, blank=True, null=True)
    purchased_by_dec_comms = models.CharField(max_length=10, blank=True, null=True)
    purchase_order = models.CharField(max_length=30, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry_date = models.DateField(blank=True, null=True)
    purchase_price = models.FloatField(blank=True, null=True)
    dec_asset = models.CharField(max_length=6, blank=True, null=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    comments = models.CharField(max_length=1000, blank=True, null=True)
    voice_number = models.CharField(max_length=20, blank=True, null=True)
    faxdata_number = models.CharField(max_length=20, blank=True, null=True)
    sim_icc_id = models.CharField(max_length=20, blank=True, null=True)
    msisdn = models.CharField(max_length=12, blank=True, null=True)
    service_provider = models.CharField(max_length=50, blank=True, null=True)
    service_plan = models.CharField(max_length=50, blank=True, null=True)
    pin_number = models.CharField(max_length=10, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_pin = models.CharField(max_length=10, blank=True, null=True)
    user_surname = models.CharField(max_length=50, blank=True, null=True)
    user_first_name = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    agency_fpcdec = models.CharField(max_length=3, blank=True, null=True)
    cost_centre = models.CharField(max_length=10, blank=True, null=True)
    chargeable_yesno = models.CharField(max_length=3, blank=True, null=True)
    registration = models.CharField(max_length=30, blank=True, null=True)
    other_information = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_conv_sat_phone_sim'


class FsConvSatSim(models.Model):
    id = models.FloatField(primary_key=True)
    supplier = models.CharField(max_length=30, blank=True, null=True)
    manufacturer = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True)
    dec_serial = models.CharField(max_length=10, blank=True, null=True)
    manufacturer_serial = models.CharField(max_length=50, blank=True, null=True)
    purchased_by_dec_comms = models.CharField(max_length=10, blank=True, null=True)
    purchase_order = models.CharField(max_length=20, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry_date = models.DateField(blank=True, null=True)
    purchase_price = models.FloatField(blank=True, null=True)
    dec_asset = models.CharField(max_length=6, blank=True, null=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    comments = models.CharField(max_length=1000, blank=True, null=True)
    voice_number = models.CharField(max_length=10, blank=True, null=True)
    faxdata_number = models.CharField(max_length=10, blank=True, null=True)
    sim_icc_id = models.CharField(max_length=20, blank=True, null=True)
    msisdn = models.CharField(max_length=12, blank=True, null=True)
    service_provider = models.CharField(max_length=50, blank=True, null=True)
    service_plan = models.CharField(max_length=50, blank=True, null=True)
    pin_number = models.CharField(max_length=10, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_pin = models.CharField(max_length=10, blank=True, null=True)
    user_surname = models.CharField(max_length=50, blank=True, null=True)
    user_first_name = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    agency_fpcdec = models.CharField(max_length=3, blank=True, null=True)
    cost_centre = models.CharField(max_length=10, blank=True, null=True)
    chargeable_yesno = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_conv_sat_sim'


class FsCostCentres(models.Model):
    cst_id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    code = models.CharField(max_length=5)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    created_by = models.CharField(max_length=30)
    created_date = models.DateField()
    cag = models.ForeignKey('FsComAgencies', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_cost_centres'


class FsDirectionTypes(models.Model):
    dir_id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    abbreviation = models.CharField(unique=True, max_length=4)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    created_by = models.CharField(max_length=30)
    created_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'fs_direction_types'


class FsDistricts(models.Model):
    dis_id = models.IntegerField(primary_key=True)
    reg = models.ForeignKey('FsRegions', models.DO_NOTHING)
    cst = models.ForeignKey('FsCostCentres', models.DO_NOTHING)
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(unique=True, max_length=4)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    created_by = models.CharField(max_length=30)
    created_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'fs_districts'
        unique_together = (('dis_id', 'reg'),)


class FsRegions(models.Model):
    reg_id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=20)
    abbreviation = models.CharField(unique=True, max_length=4)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    created_by = models.CharField(max_length=30)
    created_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'fs_regions'


class FsResOrganisations(models.Model):
    ror_id = models.IntegerField(primary_key=True)
    organisation_type = models.CharField(max_length=1)
    organisation_name = models.CharField(unique=True, max_length=30)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)
    description = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_res_organisations'


class FsResPeople(models.Model):
    emp_no = models.IntegerField(primary_key=True)
    fire_duties = models.CharField(max_length=1)
    checked = models.CharField(max_length=1)
    medical_status = models.CharField(max_length=1)
    fitness_status = models.CharField(max_length=1)
    surname = models.CharField(max_length=30)
    first_name = models.CharField(max_length=30)
    emp_status = models.CharField(max_length=5)
    gender = models.CharField(max_length=1)
    dob = models.DateField()
    commence_date = models.DateField()
    occup_term_date = models.DateField()
    ror = models.ForeignKey('FsResOrganisations', models.DO_NOTHING)
    cst = models.ForeignKey('FsCostCentres', models.DO_NOTHING)
    rpl = models.ForeignKey('FsResPhysicalLocations', models.DO_NOTHING)
    ral = models.ForeignKey('FsResAdminLocations', models.DO_NOTHING, blank=True, null=True)
    award = models.CharField(max_length=5, blank=True, null=True)
    report_level = models.CharField(max_length=1, blank=True, null=True)
    reg = models.ForeignKey('FsRegions', models.DO_NOTHING, blank=True, null=True)
    dis = models.ForeignKey('FsDistricts', models.DO_NOTHING, blank=True, null=True)
    rtn = models.ForeignKey('FsResTeamNames', models.DO_NOTHING, blank=True, null=True)
    rar_id = models.IntegerField(blank=True, null=True)
    comments = models.CharField(max_length=250, blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)
    allergies = models.CharField(max_length=250, blank=True, null=True)
    food_req = models.CharField(max_length=250, blank=True, null=True)
    ppl = models.ForeignKey('FsPeople', models.DO_NOTHING, blank=True, null=True)
    mandatory_preseason_status = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_res_people'
        unique_together = (('surname', 'first_name', 'dob', 'gender'),)


class FsResPhysicalLocations(models.Model):
    rpl_id = models.IntegerField(primary_key=True)
    physical_location = models.CharField(unique=True, max_length=50)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)
    reg = models.ForeignKey('FsRegions', models.DO_NOTHING, blank=True, null=True)
    dis = models.ForeignKey('FsDistricts', models.DO_NOTHING, blank=True, null=True)
    report_level = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_res_physical_locations'


class FsPeople(models.Model):
    ppl_id = models.IntegerField(primary_key=True)
    employee_field = models.CharField(db_column='employee#', max_length=8, blank=True, null=True)  # Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    surname = models.CharField(max_length=50, blank=True, null=True)
    initials = models.CharField(max_length=3, blank=True, null=True)
    first_name = models.CharField(max_length=16, blank=True, null=True)
    second_name = models.CharField(max_length=16, blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    occup_type = models.CharField(max_length=3, blank=True, null=True)
    current_commence = models.DateField(blank=True, null=True)
    job_term_date = models.DateField(blank=True, null=True)
    occup_commence_date = models.DateField(db_column='occup__commence_date', blank=True, null=True)  # Field renamed because it contained more than one '_' in a row.
    occup_end_date = models.DateField(blank=True, null=True)
    position_field = models.CharField(db_column='position#', max_length=10, blank=True, null=True)  # Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    occup_pos_title = models.CharField(max_length=100, blank=True, null=True)
    clevel1 = models.CharField(max_length=3, blank=True, null=True)
    clevel5 = models.CharField(max_length=15, blank=True, null=True)
    award = models.CharField(max_length=5, blank=True, null=True)
    classification = models.CharField(max_length=5, blank=True, null=True)
    step_field = models.CharField(db_column='step#', max_length=3, blank=True, null=True)  # Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    emp_status = models.CharField(max_length=5, blank=True, null=True)
    emp_stat_desc = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=5, blank=True, null=True)
    location_desc = models.CharField(max_length=50, blank=True, null=True)
    paypoint = models.CharField(max_length=5, blank=True, null=True)
    paypoint_desc = models.CharField(max_length=50, blank=True, null=True)
    date_modified = models.DateField(blank=True, null=True)
    modified_by = models.CharField(max_length=30, blank=True, null=True)
    date_created = models.DateField(blank=True, null=True)
    created_by = models.CharField(max_length=30, blank=True, null=True)
    alias = models.CharField(max_length=30, blank=True, null=True)
    mobile_phone = models.CharField(max_length=10, blank=True, null=True)
    office_phone = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fs_people'
        unique_together = (('first_name', 'surname', 'gender', 'date_of_birth'),)


class FsResTeamNames(models.Model):
    rtn_id = models.IntegerField(primary_key=True)
    team_name = models.CharField(unique=True, max_length=30)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_res_team_names'


class FsResAdminLocations(models.Model):
    ral_id = models.IntegerField(primary_key=True)
    admin_location = models.CharField(unique=True, max_length=50)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_res_admin_locations'


class FsSites(models.Model):
    sit_id = models.IntegerField(primary_key=True)
    reg = models.ForeignKey('FsRegions', models.DO_NOTHING, blank=True, null=True)
    dis = models.ForeignKey('FsDistricts', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=100)
    address_line_1 = models.CharField(max_length=100, blank=True, null=True)
    address_line_2 = models.CharField(max_length=100, blank=True, null=True)
    address_line_3 = models.CharField(max_length=100, blank=True, null=True)
    town_suburb = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.IntegerField(blank=True, null=True)
    state = models.CharField(max_length=3, blank=True, null=True)
    latitude_dec = models.FloatField(blank=True, null=True)
    longitude_dec = models.FloatField(blank=True, null=True)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    date_modified = models.DateField()
    modified_by = models.CharField(max_length=30)
    date_created = models.DateField()
    created_by = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'fs_sites'
        unique_together = (('name', 'effective_from'),)

class FsVehicleDetails(models.Model):
	
	dept =  models.CharField(max_length=6, blank=True, null=True)
	vehicle_id = models.IntegerField(primary_key=True)
	rego = models.CharField(max_length=20, blank=True, null=True)
	make_id = models.IntegerField(blank=True, null=True)
	make_desc = models.CharField(max_length=110, blank=True, null=True)
	model_id = models.IntegerField(blank=True, null=True)
	model_desc = models.CharField(max_length=110, blank=True, null=True)
	kms = models.IntegerField(blank=True, null=True)
	light_flag = models.NullBooleanField(default=None)
	category_id = models.IntegerField(blank=True, null=True)
	category_desc = models.CharField(max_length=160, blank=True, null=True)
	rate = models.IntegerField(blank=True, null=True)
	default_job_id = models.CharField(max_length=40, blank=True, null=True)
	month_cost = models.IntegerField(blank=True, null=True)
	status_flag = models.CharField(max_length=4, blank=True, null=True)
	cost_centre = models.CharField(max_length=20, blank=True, null=True)
	total_cost = models.IntegerField(blank=True, null=True)
	manufactured_mth_yr = models.DateField(blank=True, null=True)
	code = models.CharField(max_length=20, blank=True, null=True)
	engine_no = models.CharField(max_length=40, blank=True, null=True)
	kilowatts = models.CharField(max_length=40, blank=True, null=True)
	diesel_flag = models.NullBooleanField(default=None)
	automatic_flag = models.NullBooleanField(default=None)
	radio_type_flag = models.NullBooleanField(default=None)
	tare = models.IntegerField(blank=True, null=True)
	aggregate = models.IntegerField(blank=True, null=True)
	gcm = models.IntegerField(blank=True, null=True)
	serial_chassis_no = models.CharField(max_length=60, blank=True, null=True)
	delete_date = models.DateField(blank=True, null=True)
	comments = models.CharField(max_length=100, blank=True, null=True)
	comments2 = models.CharField(max_length=100, blank=True, null=True)
	comments3 = models.CharField(max_length=100, blank=True, null=True)
	location = models.CharField(max_length=100, blank=True, null=True)
	fire_unit_no = models.CharField(max_length=10, blank=True, null=True)
	file_ref = models.CharField(max_length=34, blank=True, null=True)
	old_rego = models.CharField(max_length=14, blank=True, null=True)

	class Meta:
		managed = False
		db_table = 'FS_VEHICLE_DETAILS_MV'
#		db_table = 'fs_sites'
