<template lang="html">
  <div>
    <b-field>
      <b-select
        v-model="bindVal"
        placeholder="Last Modified"
        icon="calendar"
        :loading="loading"
      >
        <option :value="null">{{ $t("none") }}</option>
        <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
      </b-select>
    </b-field>
  </div>
</template>

<script>
export default {
  name: "SelectYearField",
  props: {
    value: {
      type: [Number, String],
      default: null
    },
    startYear: {
      type: Number,
      default: 1980
    },
    finishYear: {
      type: Number,
      default: new Date().getFullYear()
    }
  },
  data() {
    return {
      loading: false,
      bindVal: this.value
    };
  },
  computed: {
    years() {
      return [...Array(new Date().getFullYear() - this.startYear).keys()].map(
        i => i + this.startYear
      );
    }
  },
  watch: {
    bindVal(val) {
      this.$emit("input", val);
    },
    value(value) {
      this.bindVal = value;
    }
  }
};
</script>

<style lang="css"></style>
