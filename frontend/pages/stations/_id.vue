<template lang="html">
  <div class="container">
    <StationHero :data="data" />
  </div>
</template>
<script>
import StationHero from "@/components/stations/StationHero";

export default {
  name: "Station",
  components: { StationHero },
  head() {
    return {
      title: this.data.short_name || this.data.id
    };
  },
  async asyncData({ params, $axios, error }) {
    try {
      let data = await $axios.$get(`/stations/${params.id}`);
      return {
        data: data
      };
    } catch (e) {
      return error({
        statusCode: 404,
        message: "station404"
      });
    }
  }
};
</script>

<style lang="css" scoped></style>
