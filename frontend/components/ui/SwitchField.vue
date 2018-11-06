<template lang="html">
  <div>
    <b-field>
      <b-switch v-model="bindVal" size="is-small"> {{ text }}</b-switch>
    </b-field>
  </div>
</template>

<script>
export default {
  name: "SwitchField",
  props: {
    text: {
      type: String,
      default: ""
    },
    loading: {
      type: Boolean,
      required: false,
      default: false
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
