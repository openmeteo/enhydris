<template lang="html">
  <div>
    <b-field>
      <b-select
        v-model="bindVal"
        :placeholder="placeholder"
        icon="globe"
        :loading="loading"
      >
        <option :value="null">{{ $t("none") }}</option>
        <option v-for="d in divisions" :key="d.id" :value="d.id"
          >{{ d.name }}
        </option>
      </b-select>
    </b-field>
  </div>
</template>

<script>
import stations from "@/api/stations.js";

export default {
  name: "SelectDivisionField",
  props: {
    value: {
      type: [Number, String],
      default: null
    }
  },
  data() {
    return {
      placeholder: this.$i18n.t("division"),
      loading: false,
      bindVal: this.value,
      divisions: []
    };
  },
  watch: {
    bindVal(val) {
      this.$emit("input", val);
    },
    value(value) {
      this.bindVal = value;
    }
  },
  mounted() {
    this.fetchDivisions();
  },
  methods: {
    async fetchDivisions() {
      this.loading = true;
      let page = 1;
      let keepGoing = true;
      while (keepGoing) {
        let { data } = await stations.divisions(page);
        if (page == 1) {
          this.loading = false;
        }
        this.divisions.push.apply(this.divisions, data.results);
        if (data.next) {
          page += 1;
        } else {
          keepGoing = false;
        }
      }
    }
  }
};
</script>

<style lang="css"></style>
