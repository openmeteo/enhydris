<template lang="html">
  <div class="container">
    <b-loading
      :is-full-page="isPageLoading"
      :active.sync="isPageLoading"
      :can-cancel="false"
    >
    </b-loading>
    <br />
    <SearchField v-model="qs" />
    <br />
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
        selectable
        @select="selected"
      >
        <template slot-scope="props">
          <b-table-column
            field="name"
            width="20"
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
            {{ props.row.water_basin ? props.row.water_basin.name : "" }}
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
      centerMap: [37.41322, -1.219482]
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
    async fetchStations() {
      this.isPageLoading = true;
      try {
        let page = 1;
        let keepGoing = true;
        while (keepGoing) {
          let data = await this.$axios.$post(`/stations?page=${page}`);
          if (page == 1) {
            this.centerMap = maputils.getBoundingBoxCenter(data.bounding_box);
            this.total = data.count;
            this.isPageLoading = false;
          }
          this.data.push.apply(this.data, data.results);
          if (data.next) {
            page += 1;
          } else {
            keepGoing = false;
          }
        }
      } catch (e) {
        this.$toast.open({
          duration: 5000,
          message: this.$i18n.t("connection_error"),
          position: "is-top",
          type: "is-danger"
        });
        this.isPageLoading = false;
        throw e;
      }
    },
    makeMarkers: function() {
      return maputils.getStationCoordinates(this.curStations);
    },
    selected(row) {
      this.$router.push(
        this.localePath({
          name: "stations-id",
          params: { id: row.id }
        })
      );
    }
  }
};
</script>

<style scoped>
table td {
  cursor: pointer;
}
</style>
