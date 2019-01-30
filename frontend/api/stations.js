import session from "./session";

export default {
  list: num => session.get(`/stations/?page=${num}`),
  types: num => session.get(`/stationtypes/?page=${num}`),
  divisions: num => session.get(`/politicaldivisions/?page=${num}`)
};
