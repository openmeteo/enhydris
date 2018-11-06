<template>
  <section>
    <DevBox />
    <nav
      class="navbar is-light enhydris-nav"
      role="navigation"
      aria-label="main navigation"
    >
      <div class="navbar-brand">
        <a class="navbar-item">
          <img
            :src="logoSrc"
            :alt="logoAlt"
            width="50"
            height="28"
          >
        </a>
      </div>
    </nav>
  </section>
</template>

<script>
import utils from "../utils";
import DevBox from "./DevBox.vue";

export default {
  name: "Navbar",
  components: {
    DevBox
  },
  data: function() {
    return {
      logoSrc: utils.get_app_logo(),
      logoAlt: utils.get_app_logo_alt()
    };
  }
};
</script>

<style scoped>
.enhydris-nav {
  margin-bottom: 0.5rem;
}
</style>
