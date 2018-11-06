import Vue from "vue";
import App from "./App.vue";
import Buefy from "buefy";
import "./../node_modules/buefy/dist/buefy.css";
import VueMoment from "vue-moment";

import router from "./router";
import store from "./store";

// Markers solution
import L from "leaflet";
delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: require("leaflet/dist/images/marker-icon-2x.png"),
  iconUrl: require("leaflet/dist/images/marker-icon.png"),
  shadowUrl: require("leaflet/dist/images/marker-shadow.png")
});

Vue.config.productionTip = false;
Vue.use(Buefy, { defaultIconPack: "fas" });
Vue.use(VueMoment);

new Vue({
  router,
  store,
  render: function(h) {
    return h(App);
  }
}).$mount("#app");
