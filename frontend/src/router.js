import Vue from "vue";
import Router from "vue-router";
import StationsList from "./views/StationsList.vue";

Vue.use(Router);

export default new Router({
  mode: "history",
  base: process.env.BASE_URL,
  routes: [
    {
      path: "/",
      name: "stations-list",
      component: StationsList
    }
  ]
});
