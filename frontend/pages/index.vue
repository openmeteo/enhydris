<template lang="html">
  <div class="container">
    <DevBox />
    <h1 style="opacity: 0.7;" class="title is-size-4 ">
      {{ $t("stations_list") }}
    </h1>
    <div>
      <h1>{{ $t("language") }}</h1>
      <nuxt-link :to="switchLocalePath('el')">Ελληνικά</nuxt-link>
      <nuxt-link :to="switchLocalePath('en')">English</nuxt-link>
    </div>
    <hr />
    <div class="box">
      <b-loading
        :is-full-page="isPageLoading"
        :active.sync="isPageLoading"
        :can-cancel="false"
      >
      </b-loading>

      <SearchField v-model="qs" />
      <div class="process-bar-wrapper  is-pulled-right">
        <FoundTag
          class="foundtag"
          :number="curStations.length"
          :loading="isPageLoading"
          :text="$t('results_found')"
        />
        <progress
          v-if="curStations.length != total"
          style="width:120px;"
          class="progress is-primary"
          :value="curStations.length"
          :max="total"
        ></progress>
      </div>
      <SwitchField
        v-model="showFilters"
        style="margin:4px 2px;"
        :text="$t('show_filters')"
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
                {{ $t("reset") }}
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
  head() {
    return {
      title: "Stations"
    };
  },
  data() {
    return {
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
    async fetchStations() {
      this.isPageLoading = true;
      let page = 1;
      let keepGoing = true;
      while (keepGoing) {
        let { data } = await stations.list(page);
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
    },
    makeMarkers: function() {
      return maputils.stationsWithMarkers(this.curStations);
    }
  }
};
</script>

<style scoped>
.process-bar-wrapper {
  display: flex;
  flex-direction: column;
}

.foundtag {
  margin: 4px 2px;
}
</style>
