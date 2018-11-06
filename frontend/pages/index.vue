<template lang="html">
  <div class="container">
    <DevBox />
    <h1 style="opacity: 0.7;" class="title is-size-4 ">{{ title }}</h1>
    <hr />
    <div class="box">
      <b-loading
        :is-full-page="isPageLoading"
        :active.sync="isPageLoading"
        :can-cancel="false"
      >
      </b-loading>

      <SearchField v-model="qs" />
      <FoundTag
        style="margin:4px 2px;"
        :number="curStations.length"
        :loading="isPageLoading"
      />
      <SwitchField
        v-model="showFilters"
        style="margin:4px 2px;"
        text="Show Filters"
      />
      <div v-if="showFilters" class="container">
        <div class="columns">
          <div class="column">
            <SelectSTypeField v-model="selectedSType" />
          </div>
          <div class="column">
            <SelectDivisionField v-model="selectedDivision" />
          </div>
          <div class="column">
            <b-field>
              <button class="button" type="button" @click="resetFilters()">
                Reset
              </button>
            </b-field>
          </div>
        </div>
      </div>
    </div>
    <no-ssr>
      <MapMarkers :zoom="3" :center="centerMap" :markers="makeMarkers()" />
    </no-ssr>
    <br />
    <div class="box" style="min-height: 800px;">
      <div v-if="curStations.length" class="dropdown is-active is-pulled-right">
        <b-select v-model="perPage">
          <option value="5">5 per page</option>
          <option value="10">10 per page</option>
          <option value="15">15 per page</option>
          <option value="20">20 per page</option>
          <option value="50">50 per page</option>
          <option value="100">100 per page</option>
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
            label="Station Name"
            sortable
          >
            {{ props.row.name }}
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
            field="copyright_holder"
            width="50"
            label="Owner"
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
              <p>Nothing here.</p>
            </div>
          </section>
        </template>
      </b-table>
    </div>
  </div>
</template>
<script>
import DevBox from "@/components/dev/DevBox.vue";
import SearchField from "@/components/ui/SearchField.vue";
import SelectSTypeField from "@/components/ui/SelectSTypeField.vue";
import SelectDivisionField from "@/components/ui/SelectDivisionField.vue";
import FoundTag from "@/components/ui/FoundTag";
import SwitchField from "@/components/ui/SwitchField";
import MapMarkers from "@/components/map/MapMarkers.vue";

import stations from "@/api/stations.js";
import maputils from "@/utils/map.js";

export default {
  name: "Stations",
  components: {
    DevBox,
    SearchField,
    SwitchField,
    FoundTag,
    SelectSTypeField,
    SelectDivisionField,
    MapMarkers
  },
  data() {
    return {
      title: "Stations List",
      qs: "",
      showFilters: false,
      isPageLoading: false,
      selectedSType: null,
      selectedDivision: null,
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
      let stype = this.selectedSType || null;
      let division = this.selectedDivision || null;
      let filtered_data = this.data
        .filter(station =>
          division ? station.political_division == division : true
        )
        .filter(station => (stype ? station.stype == stype : true))
        .filter(station => station.name.match(name_re));

      filtered_data.map(obj => {
        obj.marker = maputils.convert2coords(obj.point);
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
    resetFilters: function() {
      this.selectedSType = null;
      this.selectedDivision = null;
    },
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
          throw e;
        });
    },
    makeMarkers: function() {
      return maputils.stationsWithMarkers(this.curStations);
    }
  }
};
</script>

<style scoped></style>
