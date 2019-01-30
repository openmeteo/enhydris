<template lang="html">
  <div>
    <b-field>
      <b-select
        v-model="bindVal"
        :placeholder="placeholder"
        icon="th-list"
        :loading="loading"
      >
        <option :value="null">{{ $t("none") }}</option>
        <option v-for="type in sTypes" :key="type.id" :value="type.id"
          >{{ type.descr }}
        </option>
      </b-select>
    </b-field>
  </div>
</template>

<script>
import stations from "@/api/stations.js";

export default {
  name: "SelectSTypeField",
  props: {
    value: {
      type: [Number, String],
      default: null
    }
  },
  data() {
    return {
      placeholder: this.$i18n.t("type"),
      loading: false,
      bindVal: this.value,
      sTypes: []
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
    this.fetchSTypes();
  },
  methods: {
    async fetchSTypes() {
      let page = 1;
      let keepGoing = true;
      while (keepGoing) {
        let { data } = await stations.types(page);
        if (page == 1) {
          this.loading = false;
        }
        this.sTypes.push.apply(this.sTypes, data.results);
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
