<template lang="html">
  <section class="hero">
    <div class="hero-body">
      <div class="container">
        <h4 class="subtitle has-text-">
          {{ getDivision() }} {{ data.altitude }} m,
          {{ data.point }}
        </h4>
        <hr />
        <h1 class="title">{{ data.name }}</h1>
        <h2 class="subtitle">{{ data.copyright_holder }} <br /></h2>
        <h3 v-for="type in data.stype" :key="type.id">
          <b-tag rounded>{{ type.descr }}</b-tag>
        </h3>
        <hr />
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: "StationHero",
  props: {
    data: {
      type: Object,
      default: () => {}
    }
  },
  methods: {
    getDivision: function() {
      // extract Division from water_basin/political_division data
      let data = this.$props.data;
      let division;
      division = data["water_basin"] ? data["water_basin"].short_code : null;
      if (!division) {
        division = data["political_division"]
          ? data["political_division"].short_code
          : null;
      }
      return division ? `${division}, ` : "";
    },
    getObject: function(key) {
      let data = this.$props.data;
      return data[key] ? data[key] : "Unknown";
    }
  }
};
</script>

<style lang="css" scoped></style>
