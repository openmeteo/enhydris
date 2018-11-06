import session from "./session";

export default {
  list() {
    return session.get("/stations");
  },
  types() {
    return session.get("/stationtypes");
  },
  divisions() {
    return session.get("/politicaldivisions");
  }
};
