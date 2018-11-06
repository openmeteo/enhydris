<template lang="html">
  <div v-if="mode != 'production'" class="dev-info">
    <div class="tags are-medium">
      <span class="tag is-success">{{ mode }}</span>
      <span class="tag is-link">{{ apiRoot }}</span>
    </div>
  </div>
</template>

<script>
import utils from "@/utils";

export default {
  name: "DevBox",
  data: function() {
    return {
      mode: utils.getAppMode(),
      apiRoot: utils.getApiRoot()
    };
  }
};
</script>

<style lang="css" scoped>
.dev-info {
  margin-top: 1rem;
  margin-bottom: 1rem;
}
</style>
