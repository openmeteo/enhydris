<template lang="html">
  <div>
    <b-field>
      <b-select
        v-model="bindVal"
        placeholder="Division"
        icon="globe"
        :loading="loading"
      >
        <option :value="null">None</option>
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
    fetchDivisions() {
      this.loading = true;
      stations
        .divisions()
        .then(({ data }) => {
          this.divisions = data;
          this.loading = false;
        })
        .catch(e => {
          this.loading = false;
          throw e;
        });
    }
  }
};
</script>

<style lang="css"></style>
