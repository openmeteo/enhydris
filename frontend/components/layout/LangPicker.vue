<template>
  <div class="navbar-item has-dropdown is-hoverable">
    <a class="navbar-link langpicker">{{ $t("language_picker") }} </a>
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
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "LangPicker",
  computed: {
    currentLanguage() {
      return this.$i18n.locale || "en";
    }
  }
};
</script>

<style scoped>
.langpicker {
  min-width: 120px;
}

.flagIcon {
  width: 20px;
  height: 20px;
  margin-right: 10px;
}
</style>
