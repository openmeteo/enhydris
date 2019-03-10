export const state = () => ({
  currentLanguage: "en",
  languages: ["en", "el"]
});

export const mutations = {
  SET_LANGUAGE(state, lang) {
    state.currentLanguage = lang;
  }
};

export const actions = {
  UPDATE_LANGUAGE({ commit }, lang) {
    commit("SET_LANGUAGE", lang);
  }
};

export const getters = {
  GET_LANGUAGE(state) {
    return state.currentLanguage;
  },
  GET_LANGUAGES(state) {
    return state.languages;
  }
};
