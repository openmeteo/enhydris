<template lang="html">
  <div class="container">
    <div>
      <h1>{{ $t("language") }}</h1>
      <nuxt-link :to="switchLocalePath('el')">Ελληνικά</nuxt-link>
      <nuxt-link :to="switchLocalePath('en')">English</nuxt-link>
    </div>
    <hr />
    <b-loading
      :is-full-page="isPageLoading"
      :active.sync="isPageLoading"
      :can-cancel="false"
    >
    </b-loading>

    <SearchField v-model="qs" />
    <no-ssr>
      <MapMarkers :zoom="3" :center="centerMap" :markers="makeMarkers()" />
    </no-ssr>
    <br />
    <div class="box" style="min-height: 800px;">
      <div v-if="curStations.length" class="dropdown is-active is-pulled-right">
        <b-select v-model="perPage">
          <option value="5">{{ $t("5perpage") }}</option>
          <option value="10">{{ $t("10perpage") }}</option>
          <option value="20">{{ $t("20perpage") }}</option>
          <option value="50">{{ $t("50perpage") }}</option>
          <option value="100">{{ $t("100perpage") }}</option>
        </b-select>
      </div>
      <br /><br />
      <b-table
        :data="curStations"
        :paginated="true"
        :hoverable="true"
        :narrowed="true"
        :total="total"
        :per-page="perPage"
      >
        <template slot-scope="props">
          <b-table-column
            field="name"
            width="100"
            :label="$t('station_name')"
            sortable
          >
            {{ props.row.name }}
          </b-table-column>
          <b-table-column
            field="water_basin"
            width="40"
            :label="$t('water_basin')"
            sortable
            numeric
          >
            {{ props.row.water_basin }}
          </b-table-column>
          <b-table-column
            field="copyright_holder"
            width="50"
            :label="$t('owner')"
            sortable
          >
            {{ props.row.copyright_holder }}
          </b-table-column>
        </template>
        <template v-if="!isPageLoading" slot="empty">
          <section class="section">
            <div class="content has-text-grey has-text-centered">
              <p>
                <b-icon icon="emoticon-sad" size="is-large" />
              </p>
              <p>{{ $t("nothing_show") }}</p>
            </div>
          </section>
        </template>
      </b-table>
    </div>
  </div>
</template>
<script>
import SearchField from "@/components/ui/SearchField.vue";
import MapMarkers from "@/components/map/MapMarkers.vue";

import stations from "@/api/stations.js";
import maputils from "@/utils/map.js";

export default {
  name: "Stations",
  components: {
    SearchField,
    MapMarkers
  },
  head() {
    return {
      title: "Stations"
    };
  },
  data() {
    return {
      qs: "",
      isPageLoading: false,
      data: [],
      currentPage: 1,
      perPage: 20,
      total: 0,
      centerMap: [37.98381, 23.727539]
    };
  },
  computed: {
    curStations() {
      let name_re = new RegExp(this.qs, "i");
      let filtered_data = this.data.filter(station =>
        station.name.match(name_re)
      );

      filtered_data.map(obj => {
        obj.coordinates = maputils.wkt2coordinates(obj.point);
        return obj;
      });
      return filtered_data;
    }
  },
  created() {
    this.isPageLoading = true;
  },
  mounted() {
    this.fetchStations();
  },
  methods: {
    fetchStations: function() {
      this.isPageLoading = true;
      stations
        .list()
        .then(({ data }) => {
          this.centerMap = maputils.getBoundingBoxCenter(data.bounding_box);
          this.data = data.results;
          this.total = data.count;
          this.isPageLoading = false;
        })
        .catch(e => {
          this.isPageLoading = false;
          this.$toast.open({
            duration: 5000,
            message: this.$i18n.t("connection_error"),
            position: "is-top",
            type: "is-danger"
          });
          throw e;
        });
    },
    makeMarkers: function() {
      return maputils.getStationCoordinates(this.curStations);
    }
  }
};
</script>

<style scoped></style>
