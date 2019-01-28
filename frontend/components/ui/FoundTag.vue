<template lang="html">
  <div class="">
    <h1 v-if="!loading" class="subtitle is-6 is-pulled-right">
      {{ text }}: <strong>{{ number }}</strong>
    </h1>
  </div>
</template>

<script>
export default {
  name: "FoundTag",
  props: {
    text: {
      type: String,
      default: ""
    },
    loading: {
      type: Boolean,
      default: false
    },
    number: {
      type: Number,
      default: 0
    }
  }
};
</script>

<style lang="css"></style>
