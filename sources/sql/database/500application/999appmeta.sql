
CREATE FUNCTION {:SCHEMA:}set_all_references() returns int as $$
BEGIN
 PERFORM {:SCHEMA:}set_reference ( 'table_info.superclass', 'table_info');
 
 PERFORM {:SCHEMA:}set_reference ( 'field_info.reference', 'table_info');
 PERFORM {:SCHEMA:}set_reference ( 'field_info.classid', 'table_info');
 PERFORM {:SCHEMA:}set_reference ( 'field_info.arrayof', 'table_info');

 PERFORM {:SCHEMA:}set_reference ( 'event.refobjectid', 'object');

 PERFORM {:SCHEMA:}set_reference ( 'note.refobjectid', 'object');

 PERFORM {:SCHEMA:}set_reference ( 'object_parameter.refobjectid', 'object');

 PERFORM {:SCHEMA:}set_reference ( 'object_flag.refobjectid', 'object');

 PERFORM {:SCHEMA:}set_reference ( 'ip_subnet.subnetgroupid', 'ip_subnet_group');

 PERFORM {:SCHEMA:}set_reference ( 'ip_reservation.ownerid', 'service');
 PERFORM {:SCHEMA:}set_reference ( 'ip_reservation.subnetid', 'ip_subnet');
 PERFORM {:SCHEMA:}set_reference ( 'ip_reservation.interfaceid', 'mac_interface');

 PERFORM {:SCHEMA:}set_reference ( 'street.cityid', 'city');

 PERFORM {:SCHEMA:}set_reference ( 'street_aggregate.streetid', 'street');

 PERFORM {:SCHEMA:}set_reference ( 'building.streetid', 'street'); 

 PERFORM {:SCHEMA:}set_reference ( 'location.buildingid', 'building');

 PERFORM {:SCHEMA:}set_reference ( 'subscriber.primarylocationid', 'location');

 PERFORM {:SCHEMA:}set_reference ( 'service.subscriberid', 'subscriber');
 PERFORM {:SCHEMA:}set_reference ( 'service.parentservice', 'service');
 PERFORM {:SCHEMA:}set_reference ( 'service.typeofservice', 'type_of_service');
 PERFORM {:SCHEMA:}set_reference ( 'service.classofservice', 'class_of_service');
 PERFORM {:SCHEMA:}set_reference ( 'service.locationid', 'location');
 
 PERFORM {:SCHEMA:}set_reference ( 'device.ownerid', 'subscriber'); 
 PERFORM {:SCHEMA:}set_reference ( 'device.parentid', 'device');
 PERFORM {:SCHEMA:}set_reference ( 'device.modelid', 'device_model');
 
 PERFORM {:SCHEMA:}set_reference ( 'device_role.deviceid', 'device');
 
 PERFORM {:SCHEMA:}set_reference ( 'cpe.deviceid', 'device');
 PERFORM {:SCHEMA:}set_reference ( 'cpe.macid', 'mac_interface');
 
 PERFORM {:SCHEMA:}set_reference ( 'docsis_cable_modem.deviceid', 'device');
 PERFORM {:SCHEMA:}set_reference ( 'docsis_cable_modem.cmtsid', 'device_role');
 PERFORM {:SCHEMA:}set_reference ( 'docsis_cable_modem.downstreamid', 'device_role');
 PERFORM {:SCHEMA:}set_reference ( 'docsis_cable_modem.hfcmacid', 'mac_interface');
 PERFORM {:SCHEMA:}set_reference ( 'docsis_cable_modem.usbmacid', 'mac_interface');
 PERFORM {:SCHEMA:}set_reference ( 'docsis_cable_modem.lanmacid', 'mac_interface');
 PERFORM {:SCHEMA:}set_reference ( 'docsis_cable_modem.mgmtmacid', 'mac_interface');
 
 PERFORM {:SCHEMA:}set_reference ( 'routeros_device.deviceid', 'device');

 PERFORM {:SCHEMA:}set_reference ( 'core_switch.deviceid', 'device');
 
 PERFORM {:SCHEMA:}set_reference ( 'core_switch_port.switchid', 'core_switch');
 PERFORM {:SCHEMA:}set_reference ( 'core_switch_port.linkedto', 'device');
    
 PERFORM {:SCHEMA:}set_reference ( 'core_router.deviceid', 'device');
 
 PERFORM {:SCHEMA:}set_reference ( 'core_router_bridged_network.routerid', 'device_role');
 PERFORM {:SCHEMA:}set_reference ( 'core_router_bridged_network.subnetid', 'ip_subnet');

 PERFORM {:SCHEMA:}set_reference ( 'core_router.deviceid', 'nat_router');

 PERFORM {:SCHEMA:}set_reference ( 'wireless.deviceid', 'device');
 PERFORM {:SCHEMA:}set_reference ( 'wireless.interfaceid', 'mac_interface');

 PERFORM {:SCHEMA:}set_reference ( 'wireless_client.deviceid', 'device');
 PERFORM {:SCHEMA:}set_reference ( 'wireless_client.interfaceid', 'mac_interface');
 PERFORM {:SCHEMA:}set_reference ( 'wireless_client.accesspointid', 'device_role');

 PERFORM {:SCHEMA:}set_reference ( 'wireless_ap.deviceid', 'device');
 PERFORM {:SCHEMA:}set_reference ( 'wireless_ap.interfaceid', 'mac_interface');

 PERFORM {:SCHEMA:}set_reference ( 'wireless_link.deviceid', 'device');
 PERFORM {:SCHEMA:}set_reference ( 'wireless_link.interfaceid', 'mac_interface');
 PERFORM {:SCHEMA:}set_reference ( 'wireless_link.otherend', 'wireless_link');
  
 PERFORM {:SCHEMA:}set_reference ( 'sip_client.deviceid', 'device');
 
 
 PERFORM {:SCHEMA:}set_reference ( 'mac_interface.ipreservationid', 'ip_reservation');
 PERFORM {:SCHEMA:}set_reference ( 'mac_interface.deviceid', 'device');
 PERFORM {:SCHEMA:}set_reference ( 'mac_interface.ownerid', 'service');
 
 RETURN 0;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION {:SCHEMA:}set_editors() returns int as $$
BEGIN
 UPDATE {:SCHEMA:}field_info SET editor_class = 'Text';
 UPDATE {:SCHEMA:}field_info SET editor_class = 'Memo' WHERE type='text';
 UPDATE {:SCHEMA:}field_info SET editor_class = 'Boolean' WHERE type='bit';
 UPDATE {:SCHEMA:}field_info SET editor_class = 'Time' WHERE type='timestamp';
 PERFORM {:SCHEMA:}set_editor_class ( 'field_info.editor_class', 'Radio', NULL );
 RETURN 0;
END;
$$ LANGUAGE plpgsql;

UPDATE {:SCHEMA:}object_txt_expressions SET objecttxtexpr = '''['' || subscriberid || ''] '' || name' WHERE objecttype='subscriber';
UPDATE {:SCHEMA:}object_txt_expressions SET objecttxtexpr = '''['' || typeid || ''] '' || name' WHERE objecttype='type_of_service';
UPDATE {:SCHEMA:}object_txt_expressions SET objecttxtexpr = '''['' || name || ''] '' || network::text' WHERE objecttype='ip_subnet';
UPDATE {:SCHEMA:}object_txt_expressions SET objecttxtexpr = '''[TABLE] '' || name' WHERE objecttype='table_info';
UPDATE {:SCHEMA:}object_txt_expressions SET objecttxtexpr = '''[FIELD] '' || path' WHERE objecttype='field_info';

