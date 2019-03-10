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

      <div id="main-nav" class="navbar-menu" :class="{ 'is-active': isOpen }">
        <div class="navbar-start">
          <a
            class="navbar-item"
            :href="currentLanguage != 'en' ? currentLanguage : ''"
          >
            {{ $t("home") }}
          </a>
        </div>
        <div class="navbar-end">
          <LangPicker />
        </div>
      </div>
    </nav>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
import LangPicker from "@/components/layout/LangPicker";

export default {
  name: "NavBar",
  components: {
    LangPicker
  },
  data() {
    return {
      isOpen: false
    };
  },
  computed: {
    ...mapGetters({
      currentLanguage: "language/GET_LANGUAGE"
    })
  }
};
</script>

<style lang="css"></style>
