<template lang="html">
  <div>
    <nav class="navbar is-dark" role="navigation" aria-label="main navigation">
      <div class="navbar-brand">
        <a
          :class="{ 'is-active': isOpen }"
          role="button"
          class="navbar-burger burger"
          aria-label="menu"
          aria-expanded="false"
          data-target="navbarBasicExample"
          @click="isOpen = !isOpen"
        >
          <span aria-hidden="true"></span>
          <span aria-hidden="true"></span>
          <span aria-hidden="true"></span>
        </a>
      </div>

      <div class="navbar-menu" :class="{ 'is-active': isOpen }">
        <div class="navbar-start">
          <nuxt-link id="home" class="navbar-item" :to="localePath('index')">{{
            $t("home")
          }}</nuxt-link>
        </div>
        <div class="navbar-end">
          <a
            v-if="adminLink"
            id="adminLink"
            class="navbar-item"
            :href="adminLink"
          >
            {{ $t("login") }}
          </a>
          <LangPicker />
        </div>
      </div>
    </nav>
  </div>
</template>

<script>
import LangPicker from "@/components/layout/LangPicker";

export default {
  name: "NavBar",
  components: {
    LangPicker
  },
  data() {
    return {
      isOpen: false,
      adminLink: process.env.adminLink
    };
  },
  computed: {
    currentLanguage() {
      return this.$i18n.locale || "en";
    }
  }
};
</script>

<style scope>
.navbar {
  padding-top: 5px;
  padding-bottom: 5px;
}
</style>
