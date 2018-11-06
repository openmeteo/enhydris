<template>
  <div class="container">
    <div style="height: 50%">
      <l-map :zoom="zoom" :center="center" style="height: 300px; width: 100;">
        <l-tile-layer :url="url" :attribution="attribution" />
        <l-marker v-for="m in markers" :key="m.id" :lat-lng="m" />
      </l-map>
    </div>
  </div>
</template>

<script>
export default {
  name: "MapMarkers",
  props: {
    zoom: {
      type: Number,
      default: 13
    },
    center: {
      type: Array,
      default: function() {
        return [37.41322, -1.219482];
      }
    },
    markers: {
      type: Array,
      default: function() {
        return [];
      }
    }
  },
  data() {
    return {
      url: "http://{s}.tile.osm.org/{z}/{x}/{y}.png",
      attribution:
        '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    };
  }
};
</script>

<style></style>
