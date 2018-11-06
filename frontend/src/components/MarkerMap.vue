<template>
  <div class="container">
    <div style="height: 50%">
      <v-map
        :zoom="zoom"
        :center="center"
        style="height: 300px; width: 200;"
      >
        <v-tilelayer
          :url="url"
          :attribution="attribution"
        />
        <v-marker
          v-for="m in markers"
          :lat-lng="m"
        />
      </v-map>
    </div>
  </div>
</template>

<script>
import Vue2Leaflet from "vue2-leaflet";

export default {
  name: "MarkerMap",
  components: {
    "v-map": Vue2Leaflet.LMap,
    "v-tilelayer": Vue2Leaflet.LTileLayer,
    "v-marker": Vue2Leaflet.LMarker
  },
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

<style>
@import "~leaflet/dist/leaflet.css";
</style>
