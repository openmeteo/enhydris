<template>
  <div class="navbar-item has-dropdown is-hoverable">
    <a class="navbar-link">{{ $t("picker_language") }} </a>
    <div class="navbar-dropdown is-hidden-mobile">
      <div>
        <nuxt-link
          v-if="currentLanguage != 'en'"
          class="navbar-item"
          :to="switchLocalePath('en')"
        >
          <img src="~/static/flags/us.svg" class="flagIcon" /> English
        </nuxt-link>
        <nuxt-link
          v-if="currentLanguage != 'el'"
          class="navbar-item"
          :to="switchLocalePath('el')"
        >
          <img src="~/static/flags/el.svg" class="flagIcon" /> Ελληνικά
        </nuxt-link>
        <nuxt-link
          v-if="currentLanguage != 'de'"
          class="navbar-item"
          :to="switchLocalePath('de')"
        >
          <img src="~/static/flags/de.svg" class="flagIcon" /> Deutsch
        </nuxt-link>
        <nuxt-link
          v-if="currentLanguage != 'fr'"
          class="navbar-item"
          :to="switchLocalePath('fr')"
        >
          <img src="~/static/flags/fr.svg" class="flagIcon" /> Français
        </nuxt-link>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from "vuex";

export default {
  name: "LangPicker",
  computed: {
    ...mapGetters({
      currentLanguage: "language/GET_LANGUAGE"
    })
  }
};
</script>

<style scoped>
.flagIcon {
  width: 20px;
  height: 20px;
  margin-right: 10px;
}
</style>
