import session from "./session";

export default {
  list: () => session.get("/stations"),
  types: () => session.get("/stationtypes"),
  divisions: () => session.get("/politicaldivisions")
};
