                    #element[key] = run_deep_value_correction(USER_ID, USER_SESSION_ID, element[key], key, i)
                        sub_process_id = uuid.uuid4()

                        #create a folder for the sub process
                        pathlib.Path(f"{temp_dir_path}/{sub_process_id}").mkdir(parents=True, exist_ok=True)
                        with open(f"""{temp_dir_path}/{sub_process_id}/data.json""", "w") as f:
                            json.dump(element[key], f)

                        sub_process_input = {  
                            "user_id": USER_ID,
                            "user_session_id": f"{USER_SESSION_ID}/{sub_process_id}",
                            "file_name": f"data.json",
                            "data_info_from_user": f"{DATA_INFO_FROM_USER} for {key} in key in element. This element is part of a list of dictionaries. This element represents {data_info['meaning_of_elements_in_data']}",
                            "message": []
                        }

                        with open(f"""{temp_dir_path}/{sub_process_id}/input.json""", "w") as f:
                            json.dump(sub_process_input, f)
                        
                        sub_process_input["retriever"] = retriever
                        
                        running_correction_on_elements_results.append({
                            "sub_process_id": sub_process_id,
                            "future": executor.submit(run_graph, sub_process_input["user_id"], sub_process_input["user_session_id"], sub_process_input["file_name"], sub_process_input["data_info_from_user"], False),
                            "key": key,
                            "element_index": i
                        })















for running_correction_on_elements_result in running_correction_on_elements_results:

            with open(f"""{temp_dir_path}/{running_correction_on_elements_result["sub_process_id"]}/out.json""", "r") as f:
                corrected_deep_value = json.load(f)
                if len(corrected_deep_value) ==1:
                    out_data[running_correction_on_elements_result["element_index"]][running_correction_on_elements_result["key"]] = corrected_deep_value[0]
                else:
                    out_data[running_correction_on_elements_result["element_index"]][running_correction_on_elements_result["key"]] = corrected_deep_value

  