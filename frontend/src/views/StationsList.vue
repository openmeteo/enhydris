<template>
  <div>
    <Navbar />
    <hr>
    <div class="container">
      <div class="box">
        <b-field>
          <b-input
            placeholder="Search"
            v-model="search_query"
            :loading="loading"
          />
        </b-field>
        <h1
          v-if="search_query || showFilters"
          class="subtitle is-6 is-pulled-right"
        >
          Stations found <strong>{{ filterData.length }}</strong>
        </h1>

        <b-field>
          <b-switch
            v-model="showFilters"
            size="is-small"
          > Show Filters</b-switch>
        </b-field>
        <div
          v-if="showFilters"
          isclass=""
        >
          <div class="columns">
            <div class="column">
              <b-field>
                <b-select
                  placeholder="Type"
                  icon="th-list"
                  icon-pack="fas"
                  v-model="selectedSType"
                  :loading="loading"
                >
                  <option :value="null">None</option>
                  <option
                    v-for="type in stationsTypes"
                    :value="type.id"
                    :key="type.id"
                  >{{ type.descr }}</option>
                </b-select>
              </b-field>
            </div>
            <div class="column">
              <b-field>
                <b-select
                  placeholder="Division"
                  icon="globe"
                  icon-pack="fas"
                  v-model="selectedDivision"
                  :loading="loading"
                >
                  <option :value="null">None</option>
                  <option
                    v-for="d in stationsDivisions"
                    :value="d.id"
                    :key="d.id"
                  >{{ d.name }}</option>
                </b-select>
              </b-field>
            </div>
            <div class="column">
              <b-field>
                <b-select
                  placeholder="Last Modified"
                  icon="calendar"
                  icon-pack="fas"
                  v-model="selectedYear"
                  :loading="loading"
                >
                  <option :value="null">None</option>
                  <option
                    v-for="d in sinceYears"
                    :value="d"
                    :key="d"
                  >{{ d }}</option>
                </b-select>
              </b-field>
            </div>
            <div class="column">
              <b-field>
                <button
                  class="button"
                  type="button"
                  @click="resetFilters()"
                >Reset</button>
              </b-field>
            </div>
          </div>
        </div>
      </div>
      <MarkerMap
        :zoom="3"
        :center="centerMap"
        :markers="makeMarkers(filterData)"
      />
      <hr>
      <div class="box">
        <div class="dropdown is-active is-pulled-right">
          <b-select v-model="perPage">
            <option value="5">5 per page</option>
            <option value="10">10 per page</option>
            <option value="15">15 per page</option>
            <option value="20">20 per page</option>
            <option value="50">50 per page</option>
            <option value="100">100 per page</option>
          </b-select>
        </div>
        <br><br>
        <b-table
          :loading="loading"
          :data="filterData"
          :paginated="true"
          :hoverable="true"
          :narrowed="true"
          :total="total"
          :per-page="perPage"
        >
          <template slot-scope="props">
            <b-table-column
              field="id"
              width="10"
              label="ID"
              sortable
              centered
            >
              {{ props.row.id }}
            </b-table-column>
            <b-table-column
              field="name"
              width="100"
              label="Station Name"
              sortable
            >
              {{ props.row.name }}
            </b-table-column>
            <b-table-column
              field="short_name"
              width="100"
              label="Short Name"
              sortable
            >
              {{ props.row.short_name }}
            </b-table-column>
            <b-table-column
              field="stype"
              width="10"
              label="Type"
              sortable
              numeric
            >
              {{ props.row.stype[0] }}
            </b-table-column>
            <b-table-column
              field="water_basin"
              width="40"
              label="Water Basin"
              sortable
              numeric
            >
              {{ props.row.water_basin }}
            </b-table-column>
            <b-table-column
              field="political_division"
              width="40"
              label="Division"
              sortable
              numeric
            >
              {{ props.row.political_division }}
            </b-table-column>
            <b-table-column
              field="copyright_holder"
              width="50"
              label="Owner"
              sortable
            >
              {{ props.row.copyright_holder }}
            </b-table-column>
            <b-table-column
              field="last_modified"
              width="100"
              label="Last Modified"
              sortable
            >
              {{ props.row.last_modified | moment("dddd, MMMM YYYY") }}
            </b-table-column>
          </template>
          <template
            v-if="!loading"
            slot="empty"
          >
            <section class="section">
              <div class="content has-text-grey has-text-centered">
                <p>
                  <b-icon
                    icon="emoticon-sad"
                    size="is-large"
                  />
                </p>
                <p>Nothing here.</p>
              </div>
            </section>
          </template>
        </b-table>
      </div>

    </div>
  </div>
</template>
<script>
import Navbar from "../components/Navbar.vue";
import MarkerMap from "../components/MarkerMap.vue";
import utils from "../utils";
import stations from "../api/stations";

export default {
  name: "StationsList",
  components: {
    Navbar,
    MarkerMap
  },
  data() {
    return {
      data: [],
      loading: false,
      showFilters: false,
      currentPage: 1,
      sinceYears: utils.yearRanger(),
      perPage: 20,
      total: 0,
      search_query: "",
      stationsTypes: [],
      selectedSType: null,
      stationsDivisions: [],
      selectedDivision: null,
      selectedYear: null,
      centerMap: [37.41322, -1.219482]
    };
  },
  methods: {
    resetFilters: function() {
      this.selectedSType = null;
      this.selectedDivision = null;
      this.selectedYear = null;
    },
    getStations() {
      this.loading = true;
      stations
        .list()
        .then(({ data }) => {
          this.centerMap = utils.get_map_center(data.bounding_box);
          this.data = data.results;
          this.total = data.count;
          this.loading = false;
        })
        .catch(e => {
          this.loading = false;
          throw e;
        });
    },
    getStationTypes() {
      stations
        .types()
        .then(({ data }) => {
          this.stationsTypes = data;
        })
        .catch(e => {
          throw e;
        });
    },
    getDivisions() {
      stations
        .divisions()
        .then(({ data }) => {
          this.stationsDivisions = data;
        })
        .catch(e => {
          throw e;
        });
    },
    makeMarkers: function(data) {
      var newdata = data
        .filter(obj => {
          if (obj.marker[0]) {
            return true;
          } else {
            return false;
          }
        })
        .map(obj => {
          return obj.marker;
        });
      return newdata;
    }
  },
  computed: {
    filterData() {
      var name_re = new RegExp(this.search_query, "i");
      let stype = this.selectedSType || null;
      let division = this.selectedDivision || null;
      let sinceYear = this.selectedYear || null;
      let filtered_data = this.data
        .filter(function(station) {
          if (division) {
            return station.political_division == division;
          } else {
            return true;
          }
        })
        .filter(function(station) {
          if (stype) {
            return station.stype == stype;
          } else {
            return true;
          }
        })
        .filter(function(station) {
          if (sinceYear) {
            return parseInt(station.last_modified) >= sinceYear;
          } else {
            return true;
          }
        })
        .filter(function(station) {
          return (
            station.name.match(name_re) || station.short_name.match(name_re)
          );
        });
      //
      filtered_data.map(obj => {
        obj.marker = utils.convert2coords(obj.point);
        return obj;
      });
      return filtered_data;
    }
  },
  mounted() {
    this.getStations();
    this.getStationTypes();
    this.getDivisions();
  }
};
</script>

<style>
@import "~leaflet/dist/leaflet.css";
</style>
