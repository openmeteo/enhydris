<template lang="html">
  <div>
    <b-field>
      <b-input
        v-model="bindVal"
        icon="search"
        :placeholder="$t('search')"
        :loading="loading"
      />
    </b-field>
  </div>
</template>

<script>
export default {
  name: "SearchField",
  props: {
    loading: {
      type: Boolean,
      required: false,
      default: false
    },
    value: {
      type: String,
      default: ""
    }
  },
  data() {
    return {
      bindVal: this.value
    };
  },
  watch: {
    bindVal(val) {
      this.$emit("input", val);
    }
  }
};
</script>

<style scoped></style>
