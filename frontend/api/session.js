import axios from "axios";
import utils from "@/utils";

const session = axios.create({
  baseURL: utils.getApiRoot(),
  timeout: 10000,
  headers: {
    "Content-Type": "application/json"
  }
});

export default session;
