
#Config data from json file
def get_data_tuple():
    print("MQTT config data")
    import json
    data_tuple = ()
    with open("mqtt_config.json") as json_data:
        data_dict = json.load(json_data)
        #
        client_id = str(data_dict.get("client_id","NoClient_id"))
        data_tuple = (str(data_dict.get("broker","NoBroker")),
                      str(data_dict.get("client_user","NoClientUser")),
                      str(data_dict.get("client_pass","NoClientPass")),
                      str(data_dict.get("brokerport","NoBrokerport")),
                      str(data_dict.get("client_id","NoClient_id")),
                      client_id+"/"+str(data_dict.get("sub_topic","NoSubTopic")),
                      client_id+"/"+str(data_dict.get("pub_topic","NoPubTopic")),
                      client_id+"/"+str(data_dict.get("pub_status","NoPubStatus")),
                      str(data_dict.get("keepalive","0"))
                      )
    print(data_tuple)
    return data_tuple




