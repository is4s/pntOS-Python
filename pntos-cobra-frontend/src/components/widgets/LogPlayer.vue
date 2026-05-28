<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/log_player/log_player_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/log_player/log_player_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';

  export const metadata: WidgetMetadata = {
    title: 'Log Player',
    bannerStyle: 'blue',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'LogPlayer'
  };
</script>

<script setup lang="ts">
  import PauseButtonIcon from '@/assets/branding/svgs/widgets/log_player/pause_button.svg';
  import PlayButtonIcon from '@/assets/branding/svgs/widgets/log_player/play_button.svg';
  import CollapsableList from '@/components/common/CollapsableList.vue';
  import { CELL_GAP, MINIMIZED_WIDGET_HEIGHT } from '@/components/WidgetGrid.vue';
  import type { BaseWidgetData } from '@/components/widgets/BaseWidget.vue';
  import BaseWidget from '@/components/widgets/BaseWidget.vue';
  import { SubscriptionMode } from '@/types';
  import { useRegistry } from '@/utils/useRegistry';
  import type { Ref } from 'vue';
  import { computed, ref } from 'vue';

  const props = defineProps<BaseWidgetData>();
  const GROUP = "ui/logplayer";

  // const requestedSpeed = useRegistry<number>(GROUP, "requested_speed", SubscriptionMode.LAST, 1);
  // const nMessages = useRegistry<number>(GROUP, "n_messages", SubscriptionMode.LAST, 0);
  // const playing = useRegistry<boolean>(GROUP, "playing", SubscriptionMode.LAST, false);
  // const collapsed = useRegistry<boolean>(GROUP, 'channels_collapsed', SubscriptionMode.LAST, false);
  // const file = useRegistry<string>(GROUP, "file", SubscriptionMode.LAST, "Choose a file.");
  // const fractionThroughFile = useRegistry<number>(GROUP, "fraction_through_file", SubscriptionMode.LAST, 0);
  // const requestedFractionThroughFile = useRegistry<number>(GROUP, "requested_fraction_through_file", SubscriptionMode.LAST, 0);
  // const time = useRegistry<number>(GROUP, "time", SubscriptionMode.LAST, 0.0);
  // const actualSpeed = useRegistry<number>(GROUP, "actual_speed", SubscriptionMode.LAST, 0.0);
  // const channels = useRegistry<Array<string>>(GROUP, "channels", SubscriptionMode.LAST, []);
  // const step = useRegistry<boolean>(GROUP, 'step', SubscriptionMode.LAST, false);

  const requestedSpeed = useRegistry<number>(GROUP, "requested_speed", SubscriptionMode.LAST);
  const nMessages = useRegistry<number>(GROUP, "n_messages", SubscriptionMode.LAST);
  const playing = useRegistry<boolean>(GROUP, "playing", SubscriptionMode.LAST);
  const collapsed = useRegistry<boolean>(GROUP, 'channels_collapsed', SubscriptionMode.LAST);
  const file = useRegistry<string>(GROUP, "file", SubscriptionMode.LAST);
  const fractionThroughFile = useRegistry<number>(GROUP, "fraction_through_file", SubscriptionMode.LAST);
  const requestedFractionThroughFile = useRegistry<number>(GROUP, "requested_fraction_through_file", SubscriptionMode.LAST);
  const time = useRegistry<number>(GROUP, "time", SubscriptionMode.LAST);
  const actualSpeed = useRegistry<number>(GROUP, "actual_speed", SubscriptionMode.LAST);
  const channels = useRegistry<Array<string>>(GROUP, "channels", SubscriptionMode.LAST);
  const step = useRegistry<boolean>(GROUP, 'step', SubscriptionMode.LAST);

  const icon = computed(() => playing.value ? PauseButtonIcon : PlayButtonIcon);

  function togglePlayPause() {
    playing.value = !playing.value;
  }

  function toggleChannelCollapse() {
    collapsed.value = !collapsed.value;
  }

  function faster() {
    if (!requestedSpeed.value) requestedSpeed.value = 1;
    requestedSpeed.value = requestedSpeed.value * 2;
  }

  function slower() {
    if (!requestedSpeed.value) requestedSpeed.value = 1;
    requestedSpeed.value = requestedSpeed.value / 2;
  }

  const maxH = computed(() => {
    if (!props.layout.h) { return 0; }
    return (MINIMIZED_WIDGET_HEIGHT * props.layout.h) // Cell height
      + (2 * CELL_GAP * (props.layout.h - 1)) // Cell gap
      - 128; // the approx. height of the upper parts of the Log Player widget
  });

  function updatePosInFile(e: Event | null) {
    if (!(e instanceof Event) || !e.target || !(e.target instanceof HTMLInputElement)) return;
    requestedFractionThroughFile.value = Number(e.target.value) / 100;
  }

  const fileInput = ref<HTMLInputElement | null>(null);

  function openDialog() {
    fileInput.value?.click();
  }

  const progress = ref(null) as Ref<number | null>;

  function execStep() {
    step.value = true;
  }

  async function uploadFile(e: Event) {
    const target = e.target as HTMLInputElement;
    const selectedFile = target.files?.[0];

    if (!selectedFile) return;

    progress.value = 0;

    const formData = new FormData();
    formData.append("file", selectedFile);

    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        progress.value = Math.round((event.loaded / event.total) * 100);
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200) {
        try {
          const data = JSON.parse(xhr.responseText) as { path: string; };
          file.value = data.path;
          progress.value = null;
          target.value = '';
        } catch (error) {
          console.error('Failed to parse upload response:', error);
          progress.value = null;
        }
      } else {
        console.error('Upload failed:', xhr.status, xhr.responseText);
        progress.value = null;
      }
    };

    xhr.onerror = () => {
      console.error('Upload failed: Network error');
      progress.value = null;
    };

    xhr.open("POST", "/upload");
    xhr.send(formData);
  }

  function stopAndClose(remove: () => void) {
    playing.value = false
    setTimeout(() => {
    remove()
  }, 100)
  }

</script>

<template>
  <BaseWidget v-bind="props" :onClose="stopAndClose">
    <div id="log-player-groups">
      <div id="log-player-top-row">
        <div id="log-player-top-row-left-box">
          <div id="log-player-upload-file-button" class="clickable-button
          hoverable-button" @click="openDialog">
            Upload File
            <input type="file" ref="fileInput" style="display: none" @change="uploadFile" accept="*.log" />
          </div>
          <div id="log-player-top-row-left-box-bottom">
            <div id="log-player-play-pause-button" @click="togglePlayPause()">
              <img :src="icon" />
            </div>
            <div id="log-player-file">
              <div id="log-player-file-name" :style="progress !== null ? 'display: none;' : ''">
                {{ file ? file.split("/").pop() : "Choose a file." }}</div>
              <progress id="log-player-file-upload-progress" :value="progress ? progress
                : 0" min="0" max="100" :style="progress === null ? 'display: none;' : ''"></progress>
            </div>

          </div>

        </div>
        <div id="log-player-top-row-right-box">
          <div id="log-player-step-button" :class="step === true ?
            'log-player-step-button-active' : ''" @click="execStep">Step</div>
          <div id="log-player-top-row-right-box-bottom">
            <div id="log-player-slower-button" @click="slower()">
              <svg width="11" height="9" viewBox="0 0 11 9" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M0.137586 4.77178L5.76141 8.93267C5.8646 9.01073 6.00907 9.02091 6.12602 8.96322C6.24296 8.90552 6.32208 8.78674 6.32208 8.66116L6.32208 5.86122L10.4669 8.93267C10.57 9.01073 10.7042 9.02091 10.8177 8.96322C10.9346 8.90552 11 8.78674 11 8.66116L11 0.339387C11 0.21042 10.9312 0.0916347 10.8143 0.0373325C10.7661 0.0135755 10.7145 -2.49584e-08 10.6629 -2.9469e-08C10.5907 -3.57837e-08 10.5219 0.0237569 10.4634 0.0678777L6.31864 3.13933L6.31864 0.339387C6.31864 0.210419 6.23953 0.0916343 6.12258 0.0373321C6.07442 0.0135751 6.01939 -4.35419e-07 5.96779 -4.3993e-07C5.89556 -4.46244e-07 5.81989 0.0237565 5.76141 0.0678773L0.137586 4.22876C0.0515951 4.29325 4.02576e-07 4.39506 3.93378e-07 4.50027C3.84181e-07 4.60548 0.0515951 4.7073 0.137586 4.77178Z"
                      fill="#040747" />
              </svg>
            </div>
            <div id="log-player-requested-rate">{{ (requestedSpeed ?? 1).toFixed(2) }}</div>
            <div id="log-player-faster-button" @click="faster()">
              <svg width="11" height="9" viewBox="0 0 11 9" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10.8624 4.22821L5.23859 0.067326C5.1354 -0.0107331 4.99093 -0.0209147 4.87398 0.0367811C4.75704 0.0944769 4.67792 0.213262 4.67792 0.338836V3.13878L0.533146 0.067326C0.429956 -0.0107331 0.29581 -0.0209147 0.182301 0.0367811C0.0653533 0.0944769 0 0.213262 0 0.338836V8.66061C0 8.78958 0.068793 8.90837 0.185741 8.96267C0.233896 8.98642 0.285491 9 0.337086 9C0.409318 9 0.478111 8.97624 0.536585 8.93212L4.68136 5.86067V8.66061C4.68136 8.78958 4.76048 8.90837 4.87742 8.96267C4.92558 8.98642 4.98061 9 5.03221 9C5.10444 9 5.18011 8.97624 5.23859 8.93212L10.8624 4.77123C10.9484 4.70675 11 4.60493 11 4.49972C11 4.39451 10.9484 4.2927 10.8624 4.22821Z"
                      fill="#040747" />
              </svg>

            </div>
          </div>
        </div>
      </div>
      <div id="log-player-slider-row">
        <input id="log-player-slider" name="log-player-slider-val" label="Position in file" title="Position in file"
               placeholder="position-in-file" :value="(fractionThroughFile ?? 0) * 100" type="range" min="0" max="100"
               @input="updatePosInFile($event)" step='0.01' />
      </div>
      <div v-if="layout.h && layout.h > 2">
        <div id="log-player-stats" hx-swap-oob="true">
          {{ (time ?? 0).toFixed(2) }}
          <svg width="1" height="6" viewBox="0 0 1 6" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="0.5" y1="-2.18557e-08" x2="0.5" y2="6" stroke="#F2F2F2" />
          </svg>
          {{ (actualSpeed ?? 0).toFixed(2) }}
          <svg width="1" height="6" viewBox="0 0 1 6" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="0.5" y1="-2.18557e-08" x2="0.5" y2="6" stroke="#F2F2F2" />
          </svg>
          {{ nMessages ?? 0 }}
        </div>
        <CollapsableList :list-title="'Channels'" :items="channels ?? []" :empty-message="'No channels detected yet...'"
                         :collapsed="collapsed ?? false" :toggle-collapse-callback="toggleChannelCollapse"
                         :max-h="maxH" />
      </div>


    </div>

  </BaseWidget>
</template>

<style lang="css" scoped>
  #log-player-groups {
    margin: 9px;
    left: 0;
    height: calc(100% - 45px);
    position: absolute;
    top: 27px;
    width: calc(100% - 18px);
    overflow: hidden;
  }

  #log-player-top-row {
    /* height: 12px; */
    display: grid;
    grid-template-columns: 3fr 1fr;
    margin-bottom: 9px;
    color: #686868;
    font-weight: 400;
    font-size: 9px;
  }


  #log-player-top-row-left-box {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 5px;
    width: 100%;
  }

  #log-player-top-row-left-box-bottom {
    height: 100%;
    display: flex;
    flex-direction: row;
    gap: 6px;
  }

  #log-player-play-pause-button {
    height: 12px;
    width: 12px;
    justify-self: start;
    display: flex;
    justify-content: center;
    justify-items: center;
    align-content: center;
    align-items: center;
    cursor: pointer;
  }

  #log-player-file {
    font-style: italic;
    overflow-x: auto;
    max-width: 100%;
  }

  #log-player-top-row-right-box {
    justify-self: end;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-content: end;
    justify-items: center;
    align-items: end;
    gap: 5px;
  }

  #log-player-top-row-right-box-bottom {
    justify-self: end;
    display: flex;
    flex-direction: row;
    justify-content: center;
    align-content: center;
    justify-items: center;
    align-items: center;
    gap: 5px;
  }

  #log-player-step-button {
    color: var(--black);
    background: var(--white-smoke);
    width: 51px;
    height: 14px;
    border-radius: 100px;
    display: flex;
    justify-content: center;
    align-content: center;
    cursor: pointer;
  }

  #log-player-upload-file-button {
    color: var(--black);
    background: var(--white-smoke);
    width: 92px;
    height: 14px;
    border-radius: 100px;
    display: flex;
    justify-content: center;
    align-content: center;
    cursor: pointer;
  }

  .log-player-step-button-active {
    filter: brightness(80%);
  }

  #log-player-slower-button,
  #log-player-faster-button {
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-content: center;
    transition: flex 0.2s ease;
  }


  #log-player-slider-row {
    height: 8px;
    width: 100%;
    display: flex;
    justify-content: center;
    align-content: center;
    justify-items: center;
    align-items: center;
  }

  #log-player-line {
    height: 2px;
    width: calc(100% - 6px);
    background: var(--platinum);
    border: 1px;
  }

  #log-player-stats {
    color: #686868;
    font-size: 9px;
    font-weight: 400;
    display: flex;
    flex-direction: row;
    justify-content: start;
    justify-items: center;
    align-items: center;
    align-content: center;
    gap: 4px;
    margin-top: 4px;
  }

  #log-player-channels-list {
    max-height: calc(100% - 12px - 9px - 8px - 4px - 12px - 4px - 9px);
    overflow-y: auto;
    margin-top: 4px;
    background: var(--white-smoke);
    border-radius: 2px;
  }


</style>
