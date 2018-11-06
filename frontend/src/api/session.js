import axios from "axios";
import utils from "../utils";

const session = axios.create({
  baseURL: utils.get_api_root(),
  timeout: 5000,
  headers: {
    "Content-Type": "application/json"
  }
});

export default session;
