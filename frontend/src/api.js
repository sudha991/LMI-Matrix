import axios from "axios";

export const processPDFs = () => {
  return axios.post("http://10.0.180.28:5000/process");
};