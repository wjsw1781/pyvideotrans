import copy
import hashlib
import math
import os
import re
import shutil
import textwrap
import time
from pathlib import Path

from pydub import AudioSegment

from videotrans import translator
from videotrans.configure import config
from videotrans.util import tools
from videotrans.recognition import run as run_recogn
from videotrans.translator import run as run_trans
from videotrans.tts import run as run_tts
import subprocess

class Runstep():

    def __init__(self, init=None, obj=None, config_params=None, parent=None):
        self.init = init
        self.obj = obj
        self.config_params = config_params
        self.precent = 1
        self.parent = parent
        self.video_codec = config.settings['video_codec']

    def _unlink(self, file):
        try:
            Path(file).unlink(missing_ok=True)
        except Exception:
            pass

    # 开始识别出字幕
    def recogn(self):
        self.precent += 3
        tools.set_process(config.transobj["kaishishibie"], btnkey=self.init['btnkey'])
        # 如果不存在视频，或存在已识别过的，或存在目标语言字幕 或合并模式，不需要识别
        if self.config_params['app_mode'] in ['hebing', 'peiyin']:
            self._unlink(self.init['shibie_audio'])
            return True
        if self._srt_vail(self.init['source_sub']):
            # 判断已存在的字幕文件中是否存在有效字幕纪录
            if self.config_params['app_mode']=='tiqu':
                shutil.copy2(self.init['source_sub'], f"{self.obj['output']}/{self.obj['raw_noextname']}.srt")
            self._unlink(self.init['shibie_audio'])
            return True

        # 分离未完成，需等待
        while not tools.vail_file(self.init['source_wav']):
            tools.set_process(config.transobj["running"], btnkey=self.init['btnkey'])
            time.sleep(1)
        # 识别为字幕
        try:
            self.precent += 5
            raw_subtitles = run_recogn(
                # faster-whisper openai-whisper googlespeech
                model_type=self.config_params['model_type'],
                # 整体 预先 均等
                type=self.config_params['whisper_type'],
                # 模型名
                model_name=self.config_params['whisper_model'],
                # 识别音频
                audio_file=self.init['shibie_audio'],
                detect_language=self.init['detect_language'],
                cache_folder=self.init['cache_folder'],
                is_cuda=self.config_params['cuda'],
                inst=self)
            self._unlink(self.init['shibie_audio'])
        except Exception as e:
            msg = f'{str(e)}{str(e.args)}'
            if re.search(r'cub[a-zA-Z0-9_.-]+?\.dll', msg, re.I | re.M) is not None:
                msg = f'【缺少cuBLAS.dll】请点击菜单栏-帮助/支持-下载cublasxx.dll,或者切换为openai模型 ' if config.defaulelang == 'zh' else f'[missing cublasxx.dll] Open menubar Help&Support->Download cuBLASxx.dll or use openai model'
            elif re.search(r'out\s+?of.*?memory', msg, re.I):
                msg = f'显存不足，请使用较小模型，比如 tiny/base/small' if config.defaulelang == 'zh' else 'Insufficient video memory, use a smaller model such as tiny/base/small'
            raise Exception(f'{msg}')
        else:
            if config.current_status=='stop':
                return True
            if not raw_subtitles or len(raw_subtitles) < 1:
                raise Exception(
                    self.obj['raw_basename'] + config.transobj['recogn result is empty'].replace('{lang}',
                                                                                                 self.config_params[
                                                                                                     'source_language']))
            self._save_srt_target(raw_subtitles, self.init['source_sub'])

            if self.obj and self.obj['output'] != self.obj['linshi_output']:
                shutil.copy2(self.init['source_sub'], f"{self.obj['output']}/{Path(self.init['source_sub']).name}")
            # 仅提取字幕
            if self.config_params['app_mode'] == 'tiqu':
                shutil.copy2(self.init['source_sub'], f"{self.obj['output']}/{self.obj['raw_noextname']}.srt")
        return True

    # 字幕是否存在并且有效
    def _srt_vail(self, file):
        if not tools.vail_file(file):
            return False
        try:
            tools.get_subtitle_from_srt(file)
        except Exception:
            self._unlink(file)
            return False
        return True

    # 翻译字幕
    def trans(self):
        self.precent += 3
        # 是否需要翻译，不是 hebing，存在识别后字幕并且不存在目标语言字幕，并且原语言和目标语言不同，则需要翻译
        if self.config_params['app_mode'] in ['hebing'] or \
                self.config_params['target_language'] == '-' or \
                self.config_params['target_language'] == self.config_params[
            'source_language'] or not tools.vail_file(self.init['source_sub']):
            return True

        config.task_countdown = 0 if self.config_params['app_mode'] == 'biaozhun_jd' else config.settings[
            'countdown_sec']

        # 如果存在目标语言字幕，前台直接使用该字幕替换
        if self._srt_vail(self.init['target_sub']):
            # 判断已存在的字幕文件中是否存在有效字幕纪录
            # 通知前端替换字幕
            with open(self.init['target_sub'], 'r', encoding="utf-8", errors="ignore") as f:
                tools.set_process(f.read().strip(), 'replace_subtitle', btnkey=self.init['btnkey'])
                if self.obj and self.obj['output'] != self.obj['linshi_output']:
                    shutil.copy2(self.init['target_sub'],
                                 f"{self.obj['output']}/{Path(self.init['target_sub']).name}")
                return True

        # 批量不允许修改字幕
        if not self.config_params['is_batch']:
            # 等待编辑原字幕后翻译,允许修改字幕
            tools.set_process(config.transobj["xiugaiyuanyuyan"], 'edit_subtitle', btnkey=self.init['btnkey'])
            while config.task_countdown > 0:
                config.task_countdown -= 1
                if config.task_countdown <= config.settings['countdown_sec']:
                    tools.set_process(f"{config.task_countdown} {config.transobj['jimiaohoufanyi']}", 'show_djs',
                                      btnkey=self.init['btnkey'])
                time.sleep(1)

            # 禁止修改字幕
            tools.set_process('translate_start', 'timeout_djs', btnkey=self.init['btnkey'])
            time.sleep(2)

        # 如果已存在目标语言字幕则跳过，比如使用已有字幕，无需翻译时
        if self._srt_vail(self.init['target_sub']):
            if self.obj and self.obj['output'] != self.obj['linshi_output'] and tools.vail_file(
                    self.init['target_sub']):
                shutil.copy2(self.init['target_sub'], f"{self.obj['output']}/{Path(self.init['target_sub']).name}")
            return True
        tools.set_process(config.transobj['starttrans'], btnkey=self.init['btnkey'])
        # 开始翻译,从目标文件夹读取原始字幕
        rawsrt = tools.get_subtitle_from_srt(self.init['source_sub'], is_file=True)
        if not rawsrt or len(rawsrt) < 1:
            raise Exception(f'{self.obj["raw_basename"]}' + config.transobj['No subtitles file'])
        # 开始翻译，禁止修改字幕
        try:
            target_srt = run_trans(
                translate_type=self.config_params['translate_type'],
                text_list=rawsrt,
                target_language_name=self.config_params['target_language'],
                set_p=True,
                inst=self,
                source_code=self.init['source_language_code'])
        except Exception as e:
            raise Exception(e)
        else:
            self._save_srt_target(target_srt, self.init['target_sub'])

            if self.obj and self.obj['output'] != self.obj['linshi_output']:
                shutil.copy2(self.init['target_sub'], f"{self.obj['output']}/{Path(self.init['target_sub']).name}")
            # 仅提取，该名字删原
            if self.config_params['app_mode'] == 'tiqu':
                shutil.copy2(self.init['target_sub'],
                             f"{self.obj['output']}/{self.obj['raw_noextname']}-{self.init['target_language_code']}.srt")

        return True

    # 配音处理
    def dubbing(self):
        self.precent += 3
        config.task_countdown = 0 if self.config_params['app_mode'] == 'biaozhun_jd' else config.settings[
            'countdown_sec']
        if self.config_params['app_mode'] in ['tiqu']:
            return True

        # 不需要配音
        if self.config_params['app_mode'] in ['hebing'] or \
                self.config_params['voice_role'] == 'No' or \
                not tools.vail_file(self.init['target_sub']):
            return True
        if tools.vail_file(self.init['target_wav']):
            if self.obj and self.obj['output'] != self.obj['linshi_output']:
                shutil.copy2(self.init['target_wav'],
                             f"{self.obj['output']}/{Path(self.init['target_wav']).name}")
            return True
        # 允许修改字幕
        if not self.config_params['is_batch']:
            tools.set_process(config.transobj["xiugaipeiyinzimu"], "edit_subtitle", btnkey=self.init['btnkey'])
            while config.task_countdown > 0:
                # 其他情况，字幕处理完毕，未超时，等待1s，继续倒计时
                time.sleep(1)
                # 倒计时中
                config.task_countdown -= 1
                if config.task_countdown <= config.settings['countdown_sec']:
                    tools.set_process(f"{config.task_countdown}{config.transobj['zidonghebingmiaohou']}",
                                      'show_djs',
                                      btnkey=self.init['btnkey'])
            # 禁止修改字幕
            tools.set_process('dubbing_start', 'timeout_djs', btnkey=self.init['btnkey'])
        tools.set_process(config.transobj['kaishipeiyin'], btnkey=self.init['btnkey'])
        time.sleep(3)
        try:
            self._exec_tts(self._before_tts())
        except Exception as e:
            raise Exception(e)
        if self.obj and self.obj['output'] != self.obj['linshi_output'] and tools.vail_file(
                self.init['target_wav']):
            shutil.copy2(self.init['target_wav'], f"{self.obj['output']}/{Path(self.init['target_wav']).name}")
        return True

    # 合并操作
    def hebing(self):
        if self.precent<95:
            self.precent += 3
        # 视频 音频 字幕 合并
        if self.config_params['app_mode'] in ['tiqu', 'peiyin']:
            return True
        try:
            self._compos_video()
        except Exception as e:
            raise Exception(e)
        self.precent = 100
        return True

    def _merge_audio_segments(self, *, queue_tts=None, video_time=0):
        merged_audio = AudioSegment.empty()
        # start is not 0
        if queue_tts[0]['start_time_source'] > 0:
            silence = AudioSegment.silent(duration=queue_tts[0]['start_time_source'])
            merged_audio += silence


        # 开始时间
        cur=queue_tts[0]['start_time_source']
        length=len(queue_tts)
        for i, it in enumerate(queue_tts):

            # 存在有效配音文件则加入，否则配音时长大于0则加入静音
            segment=None
            the_ext = it['filename'].split('.')[-1]

            # 原始字幕时长
            raw_source=it['end_time_source']-it['start_time_source']
            if raw_source==0:
                continue
            # 存在配音文件
            if tools.vail_file(it['filename']):
                segment = AudioSegment.from_file(it['filename'], format="mp4" if the_ext == 'm4a' else the_ext)
                it['dubb_time']=len(segment)

            else:
                # 不存在配音文件
                segment = AudioSegment.silent(duration=raw_source)
                it['dubb_time']=raw_source

            if i==0:
                it['start_time']=it['start_time_source']
                it['end_time']=it['start_time_source']+it['dubb_time']
                cur=it['end_time']
                merged_audio+=segment
            else:
                if it['start_time_source']<cur:
                    # 如果开始时间和上一个结束片段重合
                    it['start_time']=cur
                    it['end_time']=it['start_time']+it['dubb_time']
                    cur=it['end_time']
                    merged_audio+=segment
                elif it['start_time_source']>=cur:
                    # 如果当前开始时间和上一个结束时间之间有间隔，则添加静音
                    if it['start_time_source']>cur:
                        merged_audio +=AudioSegment.silent(duration=it['start_time_source']-cur)
                    it['start_time']=it['start_time_source']
                    it['end_time']=it['start_time']+it['dubb_time']
                    merged_audio+=segment
                    cur=it['end_time']

            if cur < it['end_time_source']:
                merged_audio += AudioSegment.silent(duration=it['end_time_source']-cur)
                cur=it['end_time_source']
                it['end_time']=cur


            print(f'{i=},{it["start_time_source"]=},{it["end_time_source"]=}')
            print(f'{i=},{it["start_time"]=},{it["end_time"]=}')




            it['startraw'] = tools.ms_to_time_string(ms=it['start_time'])
            it['endraw'] = tools.ms_to_time_string(ms=it['end_time'])
            queue_tts[i]=it
            tools.set_process(text=f"audio concat:{i}", btnkey=self.init['btnkey'])



        print(f'合成音频后时长={len(merged_audio)},{video_time=}')
        # 移除尾部静音

        if not self.config_params['video_autorate'] and video_time > 0 and merged_audio and (len(merged_audio) < video_time):
            # 末尾补静音
            silence = AudioSegment.silent(duration=video_time - len(merged_audio))
            merged_audio += silence

        # 创建配音后的文件
        try:
            wavfile = self.init['cache_folder'] + "/target.wav"
            merged_audio.export(wavfile, format="wav")

            if self.config_params['app_mode'] == 'peiyin' and tools.vail_file(self.init['background_music']):
                cmd = ['-y', '-i', wavfile, '-i', self.init['background_music'], '-filter_complex',
                       "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2", '-ac', '2',
                       self.init['target_wav']]
                tools.runffmpeg(cmd)
            else:
                tools.wav2m4a(wavfile, self.init['target_wav'])
        except Exception as e:
            raise Exception(f'[error]merged_audio:{str(e)}')
        print(f'合成音频返回时 {len(merged_audio)=}')
        return len(merged_audio), queue_tts

    # 保存字幕文件 到目标文件夹
    def _save_srt_target(self, srtstr, file):
        # 是字幕列表形式，重新组装
        if isinstance(srtstr, list):
            txt = ""
            line=0
            for it in srtstr:
                line+=1
                if "startraw" not in it:
                    startraw, endraw = it['time'].strip().split(" --> ")
                    startraw = startraw.strip().replace('.', ',')
                    endraw = endraw.strip().replace('.', ',')
                    startraw = tools.format_time(startraw, ',')
                    endraw = tools.format_time(endraw, ',')
                else:
                    startraw=it['startraw']
                    endraw=it['endraw']
                txt += f"{line}\n{startraw} --> {endraw}\n{it['text']}\n\n"
            with open(file, 'w', encoding="utf-8") as f:
                f.write(txt)
            time.sleep(1)
            tools.set_process(txt, 'replace_subtitle', btnkey=self.init['btnkey'])
        return True

    # 配音预处理，去掉无效字符，整理开始时间
    def _before_tts(self):
        # 整合一个队列到 exec_tts 执行
        if self.config_params['voice_role'] == 'No':
            return True
        queue_tts = []
        # 获取字幕
        try:
            subs = tools.get_subtitle_from_srt(self.init['target_sub'])
            if len(subs) < 1:
                raise Exception("字幕格式不正确，请打开查看")
        except Exception as e:
            raise Exception(f'格式化字幕失败:{str(e)}')
        rate = int(str(self.config_params['voice_rate']).replace('%', ''))
        if rate >= 0:
            rate = f"+{rate}%"
        else:
            rate = f"{rate}%"
        # 取出设置的每行角色
        line_roles = self.config_params["line_roles"] if "line_roles" in self.config_params else None
        # 取出每一条字幕，行号\n开始时间 --> 结束时间\n内容
        for i, it in enumerate(subs):
            # 判断是否存在单独设置的行角色，如果不存在则使用全局
            voice_role = self.config_params['voice_role']
            if line_roles and f'{it["line"]}' in line_roles:
                voice_role = line_roles[f'{it["line"]}']
            newrole = voice_role.replace('/', '-').replace('\\', '/')
            filename = f'{i}-{newrole}-{self.config_params["voice_rate"]}-{self.config_params["voice_autorate"]}-{it["text"]}-{self.config_params["volume"].replace("%", "")}-{self.config_params["pitch"]}'
            md5_hash = hashlib.md5()
            md5_hash.update(f"{filename}".encode('utf-8'))
            # 要保存到的文件
            # clone-voice同时也是音色复制源
            filename = self.init['cache_folder'] + "/" + md5_hash.hexdigest() + ".mp3"
            # 如果是clone-voice类型， 需要截取对应片段
            if it['end_time'] <= it['start_time']:
                continue
            if self.config_params['tts_type'] == 'clone-voice':
                if self.config_params['is_separate'] and not tools.vail_file(self.init['vocal']):
                    raise Exception(f"背景分离出错 {self.init['vocal']}")
                    # clone 方式文件为wav格式
                if self.config_params['app_mode'] != 'peiyin' and tools.vail_file(self.init['source_wav']):
                    tools.cut_from_audio(
                        audio_file=self.init['vocal'] if self.config_params[
                            'is_separate'] else self.init['source_wav'],
                        ss=it['startraw'],
                        to=it['endraw'],
                        out_file=filename
                    )

            queue_tts.append({
                "text": it['text'],
                "role": voice_role,
                "start_time": it['start_time'],
                "end_time": it['end_time'],
                "rate": rate,
                "startraw": it['startraw'],
                "endraw": it['endraw'],
                "volume": self.config_params['volume'],
                "pitch": self.config_params['pitch'],
                "tts_type": self.config_params['tts_type'],
                "filename": filename})
        return queue_tts

    # 1. 将每个配音的实际长度加入 dubb_time
    def _add_dubb_time(self, queue_tts):
        for i, it in enumerate(queue_tts):
            tools.set_process(text=f"audio:{i}", btnkey=self.init['btnkey'])
            # 防止开始时间比上个结束时间还小
            if i > 0 and it['start_time'] < queue_tts[i - 1]['end_time']:
                it['start_time'] = queue_tts[i - 1]['end_time']
            # 防止结束时间小于开始时间
            if it['end_time'] < it['start_time']:
                it['end_time'] = it['start_time']
            # 保存原始字幕时间戳
            it['start_time_source'] = it['start_time']
            it['end_time_source'] = it['end_time']
            # 记录原始字幕区间时长,不随去除字幕间空白、加速等变化，永远固定
            it['raw_duration_source'] = it['end_time'] - it['start_time']

            # 会随去除字幕间空白、加速等变化
            it['raw_duration'] = it['end_time'] - it['start_time']

            # -1代表未经过音频加速，仅仅进行视频慢速处理
            # 0 代表经过了音频慢速，但是视频无需加速
            # >0 需要视频慢放到的实际时长
            it['video_extend']=-1

            # 记录实际配音后，未经任何处理的真实配音时长
            if tools.vail_file(it['filename']):
                the_ext = it['filename'].split('.')[-1]
                it['dubb_time'] = len(
                    AudioSegment.from_file(it['filename'], format="mp4" if the_ext == 'm4a' else the_ext))
            else:
                # 不存在配音
                it['dubb_time'] = 0
                it['video_extend']=0
            queue_tts[i] = it

        return queue_tts

    # 2.  移除原字幕多于配音的时长，实际是字幕结束时间向前移动，和下一条之间的空白更加多了
    # 配音时长不变， end_time 时间戳变化， raw_duration变化
    def _remove_srt_silence(self, queue_tts):
        # 如果需要移除多出来的静音
        for i, it in enumerate(queue_tts):
            # 配音小于 原时长，移除默认静音
            if it['dubb_time'] > 0 and it['dubb_time'] < it['raw_duration']:
                diff = it['raw_duration'] - it['dubb_time']
                it['end_time'] -= diff
                it['endraw']=tools.ms_to_time_string(ms=it['end_time'])
                it['raw_duration'] = it['dubb_time']
            queue_tts[i] = it
        return queue_tts

    #   移除2个字幕间的空白间隔 config.settings[remove_white_ms] ms
    # 配音时长不变。raw_duration不变
    def _remove_white_ms(self, queue_tts):
        offset = 0
        for i, it in enumerate(queue_tts):
            if i > 0:
                it['start_time'] -= offset
                it['end_time'] -= offset
                # 配音小于 原时长，移除默认静音
                dt = it['start_time'] - queue_tts[i - 1]['end_time']
                if dt > config.settings['remove_white_ms']:
                    diff = config.settings['remove_white_ms'] if config.settings['remove_white_ms']>-1 else dt
                    it['end_time'] -= diff
                    it['start_time'] -= diff
                    offset += diff
                it['startraw']=tools.ms_to_time_string(ms=it['start_time'])
                it['endraw']=tools.ms_to_time_string(ms=it['end_time'])
                queue_tts[i] = it
        return queue_tts

    # 2. 先对配音加速，每条字幕信息中写入加速倍数 speed和延长的时间 add_time
    def _ajust_audio(self, queue_tts):
        # 遍历所有字幕条， 计算应该的配音加速倍数和延长的时间
        length=len(queue_tts)
        video_time = tools.get_video_duration(self.init['novoice_mp4'])
        for i, it in enumerate(queue_tts):
            # 是否需要音频加速
            it['speed'] = False
            # 存在配音时进行处理 没有配音
            if it['dubb_time'] <= 0 or it['end_time'] == it['start_time']:
                queue_tts[i] = it
                continue

            # 可用时长，从本片段开始到下一个片段开始
            able_time=queue_tts[i+1]['start_time']-it['start_time'] if i<length-1 else video_time-it['start_time']
            # 配音时长小于等于可用时长，无需加速
            if it['dubb_time']<=able_time:
                queue_tts[i]=it
                continue

            it['speed'] = True
            queue_tts[i] = it

        # 允许最大音频加速倍数
        max_speed=float(config.settings['audio_rate'])
        for i, it in enumerate(queue_tts):
            jindu = (length* 10) / (i + 1)
            if self.precent + jindu < 95:
                self.precent += jindu
            # 不需要或不存在配音文件 跳过
            if not it['speed'] or not tools.vail_file(it['filename']):
                continue

            tools.set_process(f"{config.transobj['dubbing speed up']} [{i}]",btnkey=self.init['btnkey'])

            # 可用时长
            able_time = queue_tts[i + 1]['start_time'] - it['start_time'] if i < length - 1 else video_time - it['start_time']
            if it['dubb_time']<=able_time:
                continue

            # 配音大于可用时长毫秒数
            diff=it['dubb_time']-able_time

            # 如果加速到恰好等于 able_time 时长，需要加速的倍数
            shound_speed=round(it['dubb_time']/able_time,2)

            # 仅当开启视频慢速，shound_speed大于1.5，diff大于1s，才考虑视频慢速
            if self.config_params['video_autorate'] and config.settings['video_rate']>1 and diff>1000 and shound_speed>1.5:
                # 开启了视频慢速，音频加速一半
                # 音频加速一半后实际时长应该变为
                audio_extend=it['dubb_time']-int(diff/2)
                print(f'[音频加速 视频慢速]音频处理，{audio_extend=}')
                # 如果音频加速一半后仍然大于设定，则重新设定加速后音频时长
                if round(it['dubb_time']/audio_extend,2)>max_speed:
                    audio_extend=int(it['dubb_time']/max_speed)
                    print(f'[音频加速 视频慢速]音频2次处理，{audio_extend=}')
            else:
                #仅处理音频加速
                if shound_speed<=max_speed:
                    audio_extend=able_time
                else:
                    audio_extend=int(it['dubb_time']/max_speed)
                print(f'仅音频加速，{shound_speed=},{audio_extend=},{it["dubb_time"]=}')


            # # 调整音频
            tmp_mp3 = f'{it["filename"]}-speed.mp3'
            tools.precise_speed_up_audio(file_path=it['filename'],
                                         out=tmp_mp3,
                                         target_duration_ms=audio_extend,
                                         max_rate=100)

            # 获取实际加速完毕后的真实配音时长，因为精确度原因，未必和上述计算出的一致
            #如果视频需要变化，更新视频时长需要变化的长度
            if tools.vail_file(tmp_mp3):
                mp3_len = len(AudioSegment.from_file(tmp_mp3, format="mp3"))
                it['filename'] = tmp_mp3
                it['dubb_time'] = mp3_len
            queue_tts[i] = it
        return queue_tts




    # 视频慢速 在配音加速调整后，根据字幕实际开始结束时间，裁剪视频，慢速播放实现对齐
    def _ajust_video(self, queue_tts):
        if not self.config_params['video_autorate'] or config.settings['video_rate'] <= 1:
            return queue_tts
        concat_txt_arr = []
        if not tools.is_novoice_mp4(self.init['novoice_mp4'], self.init['noextname']):
            raise Exception("not novoice mp4")
        # 获取视频时长
        last_time = tools.get_video_duration(self.init['novoice_mp4'])
        self.parent.status_text = config.transobj['videodown..']

        length=len(queue_tts)
        max_pts=config.settings['video_rate']
        # 按照原始字幕截取
        for i, it in enumerate(queue_tts):
            jindu = (length * 10) / (i + 1)
            if self.precent + jindu < 95:
                self.precent += jindu

            # 可用的时长
            able_time=it['end_time_source']-it['start_time_source']
            # 视频需要和配音对齐，video_extend是需要增加的时长
            it['video_extend']=it['dubb_time']-able_time
            queue_tts[i]=it

            # 如果i==0即第一个视频，前面若是还有片段，需要截取
            if i == 0:
                #如果前面有大于 0 的片段，需截取
                if it['start_time_source'] > 0:
                    before_dst = self.init['cache_folder'] + f'/{i}-before.mp4'
                    # 下一片段起始时间
                    st_time=it['start_time_source']
                    try:
                        tools.cut_from_video(ss='00:00:00.000',
                                             to=tools.ms_to_time_string(ms=it['start_time_source']),
                                             source=self.init['novoice_mp4'],
                                             out=before_dst)
                        concat_txt_arr.append(before_dst)
                    except Exception:
                        pass
                else:
                    # 下一片段起始时间,从视频开始处
                    st_time=0

                # 当前视频实际时长
                duration=it['end_time_source']- st_time
                # 是否需要延长视频
                pts=""
                if it['video_extend']>0:
                    pts=round((it['video_extend']+duration)/duration,2)
                    if pts>max_pts:
                        print(f'{i=},{pts=} > {max_pts=}')
                        pts=max_pts
                        it['video_extend']=duration*max_pts-duration
                    print(f'{i}/{length},{it["dubb_time"]=},{able_time=},视频应延长{it["video_extend"]}ms,pts={pts}')
                tools.set_process(f"{config.transobj['videodown..']} {pts=}",btnkey=self.init['btnkey'])
                before_dst = self.init['cache_folder'] + f'/{i}-current.mp4'
                try:
                    tools.cut_from_video(
                        ss= '00:00:00.000' if st_time==0 else tools.ms_to_time_string(ms=st_time),
                         to=tools.ms_to_time_string(ms=it['end_time_source']),
                         source=self.init['novoice_mp4'],
                         pts=pts,
                         out=before_dst
                    )
                    concat_txt_arr.append(before_dst)
                    it['video_extend']=tools.get_video_duration(before_dst)-duration
                except Exception:
                    pass
            else:
                # 距离前面一个的时长
                diff=it['start_time_source']-queue_tts[i - 1]['end_time_source']
                if diff>0:
                    before_dst = self.init['cache_folder'] + f'/{i}-before.mp4'
                    st_time=it['start_time_source']
                    try:
                        tools.cut_from_video(
                            ss=tools.ms_to_time_string(ms=queue_tts[i - 1]['end_time_source']),
                             to=tools.ms_to_time_string(ms=it['start_time_source']),
                             source=self.init['novoice_mp4'],
                             out=before_dst
                        )
                        concat_txt_arr.append(before_dst)
                    except Exception:
                        pass
                else:
                    st_time=queue_tts[i - 1]['end_time_source']

                # 是否需要延长视频
                pts = ""
                duration = it['end_time_source'] - st_time
                if it['video_extend'] > 0:
                    pts = round((it['video_extend']+duration) / duration, 2)
                    if pts>max_pts:
                        print(f'{i=},{pts=} > {max_pts=}')
                        pts=max_pts
                        it['video_extend']=duration*max_pts-duration
                    print(f'{i}/{length},{it["dubb_time"]=},{able_time=},视频应延长{it["video_extend"]}ms,pts={pts}')
                tools.set_process(f"{config.transobj['videodown..']} {pts=}",btnkey=self.init['btnkey'])
                before_dst = self.init['cache_folder'] + f'/{i}-current.mp4'

                try:
                    tools.cut_from_video(ss=tools.ms_to_time_string(ms=st_time),
                                         to=tools.ms_to_time_string(ms=it['end_time_source']),
                                         source=self.init['novoice_mp4'],
                                         pts=pts,
                                         out=before_dst)
                    concat_txt_arr.append(before_dst)
                    it['video_extend']=tools.get_video_duration(before_dst)-duration

                except Exception:
                    pass
                # 是最后一个，并且未到视频末尾
                if i==length-1 and it['end_time_source']<last_time:
                    # 最后一个
                    before_dst = self.init['cache_folder'] + f'/{i}-after.mp4'
                    try:
                        tools.cut_from_video(ss=tools.ms_to_time_string(ms=it['end_time_source']),
                                             source=self.init['novoice_mp4'],
                                             out=before_dst)
                        concat_txt_arr.append(before_dst)
                    except Exception:
                        pass

        # 需要调整 原字幕时长，延长视频相当于延长了原字幕时长
        offset=0
        for i,it in enumerate(queue_tts):
            it['start_time_source']+=offset
            it['end_time_source']+=offset
            if it['video_extend']>0:
                it['end_time_source']+=it['video_extend']
                offset+=it['video_extend']
            queue_tts[i]=it

        # 将所有视频片段连接起来
        new_arr = []
        for it in concat_txt_arr:
            if tools.vail_file(it):
                new_arr.append(it)
        if len(new_arr) > 0:
            tools.set_process(f"连接视频片段..." if config.defaulelang == 'zh' else 'concat multi mp4 ...', btnkey=self.init['btnkey'])
            tools.concat_multi_mp4(filelist=concat_txt_arr, out=self.init['novoice_mp4'])
        return queue_tts

    def _exec_tts(self, queue_tts):
        if not queue_tts or len(queue_tts) < 1:
            raise Exception(f'Queue tts length is 0')
        # 具体配音操作
        try:
            run_tts(queue_tts=copy.deepcopy(queue_tts), language=self.init['target_language_code'], set_p=True,inst=self)
        except Exception as e:
            raise Exception(e)

        # 1.首先添加配音时间
        queue_tts = self._add_dubb_time(queue_tts)

        # 2.移除字幕多于配音的时间，实际上是字幕结束时间前移，和下一条字幕空白更多
        if config.settings['remove_srt_silence']:
            queue_tts = self._remove_srt_silence(queue_tts)


        # 5.从字幕间隔移除多余的毫秒数
        if config.settings['remove_white_ms'] > 0:
            queue_tts = self._remove_white_ms(queue_tts)

        # 4. 如果需要配音加速
        if self.config_params['voice_autorate'] and config.settings['audio_rate'] > 1:
            queue_tts = self._ajust_audio(queue_tts)

        # 如果仅需配音
        if self.config_params['app_mode'] == 'peiyin':
            segments = []
            start_times = []
            for i, it in enumerate(queue_tts):
                if it['dubb_time'] > 0 and tools.vail_file(it['filename']):
                    the_ext = it['filename'].split('.')[-1]
                    segments.append(
                        AudioSegment.from_file(it['filename'], format="mp4" if the_ext == 'm4a' else the_ext))
                    start_times.append(it['start_time'])
                else:
                    segments.append(AudioSegment.silent(duration=it['end_time'] - it['start_time']))
            self._merge_audio_segments(queue_tts=queue_tts)
            return True

        # 6.处理视频慢速
        video_time = tools.get_video_duration(self.init['novoice_mp4'])
        print(f'视频慢速前时长{video_time=}')
        if self.config_params['video_autorate'] and config.settings['video_rate'] > 1:
            queue_tts = self._ajust_video(queue_tts)

        # 获取 novoice_mp4的长度
        if not tools.is_novoice_mp4(self.init['novoice_mp4'], self.init['noextname']):
            raise Exception("not novoice mp4")
        video_time = tools.get_video_duration(self.init['novoice_mp4'])
        print(f'视频慢速后时长{video_time=}')
        audio_length, queue_tts = self._merge_audio_segments(
            video_time=video_time,
            queue_tts=copy.deepcopy(queue_tts))



        # 更新字幕
        srt = ""
        for (idx, it) in enumerate(queue_tts):
            if not config.settings['force_edit_srt']:
                it['startraw'] = tools.ms_to_time_string(ms=it['start_time_source'])
                it['endraw'] = tools.ms_to_time_string(ms=it['end_time_source'])
            srt += f"{idx + 1}\n{it['startraw']} --> {it['endraw']}\n{it['text']}\n\n"
        # 字幕保存到目标文件夹
        with open(self.init['target_sub'], 'w', encoding="utf-8", errors="ignore") as f:
            f.write(srt.strip())

        return True

    # 延长 novoice.mp4  duration_ms 毫秒
    def _novoicemp4_add_time(self, duration_ms):
        if duration_ms < 1000:
            return
        tools.set_process(f'{config.transobj["shipinmoweiyanchang"]} {duration_ms}ms', btnkey=self.init['btnkey'])
        if not tools.is_novoice_mp4(self.init['novoice_mp4'], self.init['noextname']):
            raise Exception("not novoice mp4")

        video_time = tools.get_video_duration(self.init['novoice_mp4'])
        shutil.copy2(self.init['novoice_mp4'],self.init['novoice_mp4']+".raw.mp4")
        try:
            tools.cut_from_video(
                source=self.init['novoice_mp4'],
                ss=tools.ms_to_time_string(ms=video_time - 500).replace(',', '.'),
                out=self.init['cache_folder'] + "/last-clip-novoice.mp4"
            )
            tools.runffmpeg([
                '-y',
                 '-stream_loop',
                f'{math.ceil(duration_ms/500)}',
                '-i',
                self.init['cache_folder'] + "/last-clip-novoice.mp4",
                '-c:v',
                'copy',
                '-an',
                self.init['cache_folder'] + "/last-clip-novoice-all.mp4"
            ])
        except Exception as  e:
            print(e)

        tools.runffmpeg([
            '-y',
            '-i',
            f"{self.init['novoice_mp4']}.raw.mp4",
            '-i',
            self.init['cache_folder'] + "/last-clip-novoice-all.mp4",
            '-filter_complex',
            "[0:v][1:v]concat=n=2:v=1[outv]",
            '-map',
            "[outv]",
            '-an',
            self.init['novoice_mp4']])

        # shutil.copy2(self.init['novoice_mp4'],self.init['novoice_mp4']+"----.mp4")
        Path(f"{self.init['novoice_mp4']}.raw.mp4").unlink(missing_ok=True)
        return True

    # 添加背景音乐
    def _back_music(self):
        if self.config_params['app_mode'] not in ["hebing", "tiqu", "peiyin"] and self.config_params[
            'voice_role'] != 'No' and tools.vail_file(self.init['target_wav']) and tools.vail_file(
            self.init['background_music']):
            try:
                # 获取视频长度
                vtime = tools.get_video_info(self.init['novoice_mp4'], video_time=True)
                vtime /= 1000
                # 获取音频长度
                atime = tools.get_audio_time(self.init['background_music'])
                # 转为m4a
                if not self.init['background_music'].lower().endswith('.m4a'):
                    tmpm4a = self.init['cache_folder'] + f"/background_music-1.m4a"
                    tools.wav2m4a(self.init['background_music'], tmpm4a)
                    self.init['background_music'] = tmpm4a
                beishu = vtime / atime
                if config.settings['loop_backaudio'] and beishu > 1 and vtime - 1 > atime:
                    beishu = int(beishu)
                    # 获取延长片段
                    # 背景音频连接延长片段
                    tools.concat_multi_audio(filelist=[self.init['background_music'] for n in range(beishu + 1)],
                                             out=self.init['cache_folder'] + "/background_music-2.m4a")
                    self.init['background_music'] = self.init['cache_folder'] + "/background_music-2.m4a"
                # 背景音频降低音量
                tools.runffmpeg(
                    ['-y', '-i', self.init['background_music'], "-filter:a",
                     f"volume={config.settings['backaudio_volume']}",
                     '-c:a', 'aac',
                     self.init['cache_folder'] + f"/background_music-3.m4a"])
                # 背景音频和配音合并
                cmd = ['-y', '-i', self.init['target_wav'], '-i',
                       self.init['cache_folder'] + f"/background_music-3.m4a",
                       '-filter_complex', "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2", '-ac', '2',
                       self.init['cache_folder'] + f"/lastend.m4a"]
                tools.runffmpeg(cmd)
                self.init['target_wav'] = self.init['cache_folder'] + f"/lastend.m4a"
            except Exception as e:
                config.logger.error(f'添加背景音乐失败:{str(e)}')

    def _separate(self):
        if self.config_params['is_separate'] and tools.vail_file(self.init['target_wav']):
            try:
                # 原始背景音乐 wav,和配音后的文件m4a合并
                # 获取视频长度
                vtime = tools.get_video_info(self.init['novoice_mp4'], video_time=True)
                vtime /= 1000
                # 获取音频长度
                atime = tools.get_audio_time(self.init['instrument'])
                if config.settings['loop_backaudio'] and atime + 1 < vtime:
                    # 延长背景音
                    cmd = ['-y', '-i', self.init['instrument'], '-ss', '00:00:00.000', '-t',
                           f'{vtime - atime}', self.init['cache_folder'] + "/yanchang.m4a"]
                    tools.runffmpeg(cmd)
                    # 背景音连接延长片段
                    tools.concat_multi_audio(
                        filelist=[self.init['instrument'], self.init['cache_folder'] + "/yanchang.m4a"],
                        out=self.init['cache_folder'] + f"/instrument-2.m4a")

                    self.init['instrument'] = self.init['cache_folder'] + f"/instrument-2.m4a"
                # 背景音合并配音
                tools.backandvocal(self.init['instrument'], self.init['target_wav'])
            except Exception as e:
                config.logger.error('合并原始背景失败' + config.transobj['Error merging background and dubbing'] + str(e))

    # 最终合成视频 source_mp4=原始mp4视频文件，noextname=无扩展名的视频文件名字
    def _compos_video(self):
        if self.config_params['app_mode'] in ['tiqu', 'peiyin']:
            return True

        # 判断novoice_mp4是否完成
        if not tools.is_novoice_mp4(self.init['novoice_mp4'], self.init['noextname']):
            raise Exception(config.transobj['fenlinoviceerror'])
        # 无声音视频 或 合并模式时原视频
        novoice_mp4_path = Path(self.init['novoice_mp4'])
        novoice_mp4 = Path(self.init['novoice_mp4']).as_posix()
        # 视频目录，用于硬字幕时进入工作目录
        mp4_dirpath = novoice_mp4_path.parent.resolve()

        # 软字幕 完整路径
        soft_srt = Path(self.init['target_sub']).as_posix()

        # 硬字幕仅名字 需要和视频在一起
        hard_srt = "tmp.srt"
        hard_srt_path = Path(mp4_dirpath / hard_srt)

        # 存放目标字幕
        target_sub_list = []
        # 存放原始字幕
        source_sub_list = []
        # 需要字幕
        if self.config_params['subtitle_type'] > 0:
            vh = ""
            try:
                remain_h = 20
                if config.settings['subtitle_bottom'] and config.settings['subtitle_bottom'] > (
                        self.init['video_info']['height'] - remain_h):
                    vh = f",MarginV={self.init['video_info']['height'] - remain_h}"
                elif config.settings['subtitle_bottom'] and config.settings['subtitle_bottom'] > 0:
                    vh = f",MarginV={vh}"
            except Exception:
                pass
            maxlen_source = config.settings['cjk_len'] if self.init['source_language_code'][:2] in ["zh", "ja", "jp","ko"] else config.settings['other_len']
            if tools.vail_file(self.init['source_sub']):
                try:
                    source_sub_list = tools.get_subtitle_from_srt(self.init['source_sub'])
                except Exception as e:
                    raise Exception(f'{config.transobj["Subtitles error"]}-1 :{str(e)}')
            #如果未设置目标语言，仅存在原始语言
            if not self.init['target_language_code']:
                if self.config_params['subtitle_type']==3:
                    self.config_params['subtitle_type']=1
                elif self.config_params['subtitle_type']==4:
                    self.config_params['subtitle_type']=2
                # 软字幕使用原始语言字幕
                soft_srt = Path(self.init['source_sub']).as_posix()
                # 硬字幕均为原始字幕
                if self.config_params['subtitle_type'] ==1:
                    text = ""
                    for i, it in enumerate(source_sub_list):
                        it['text'] = textwrap.fill(it['text'], maxlen_source,replace_whitespace=False).replace('\n', '\\N')
                        text += f"{it['line']}\n{it['time']}\n{it['text'].strip()}\n\n"
                    hard_srt_path.write_text(text, encoding='utf-8', errors="ignore")
                    os.chdir(mp4_dirpath)
                    hard_srt = tools.set_ass_font(hard_srt_path.as_posix())
            else:
                #存在目标语言
                maxlen = config.settings['cjk_len'] if self.init['target_language_code'][:2] in ["zh", "ja", "jp","ko"] else config.settings['other_len']
                try:
                    target_sub_list = tools.get_subtitle_from_srt(self.init['target_sub'])
                    # 提前处理单硬字幕
                    if self.config_params['subtitle_type'] in [1, 3]:
                        text = ""
                        for i, it in enumerate(target_sub_list):
                            it['text'] = textwrap.fill(it['text'], maxlen, replace_whitespace=False).replace('\n', '\\N')
                            text += f"{it['line']}\n{it['time']}\n{it['text'].strip()}\n\n"
                        hard_srt_path.write_text(text, encoding='utf-8', errors="ignore")
                        os.chdir(mp4_dirpath)
                        hard_srt = tools.set_ass_font(hard_srt_path.as_posix())
                except Exception as e:
                    raise Exception(f'{config.transobj["Subtitles error"]}-1 :{str(e)}')


        if self.precent < 90:
            self.precent = 90

        # 如果是合并字幕模式 双字幕强制为单
        if self.config_params['app_mode'] == 'hebing':
            if self.config_params['subtitle_type'] in [1, 3]:
                tools.runffmpeg([
                    "-y",
                    "-i",
                    novoice_mp4,
                    "-c:v",
                    f"libx{self.video_codec}",
                    "-vf",
                    f"subtitles={hard_srt}",
                    '-crf',
                    f'{config.settings["crf"]}',
                    '-preset',
                    config.settings['preset'],
                    Path(self.init['targetdir_mp4']).as_posix(),
                ])
            else:
                # 软字幕
                tools.runffmpeg([
                    "-y",
                    "-i",
                    novoice_mp4,
                    "-i",
                    soft_srt,
                    "-c:v",
                    "copy" if self.init['h264'] else f"libx{self.video_codec}",
                    "-c:s",
                    "mov_text",
                    "-metadata:s:s:0",
                    f"language=eng",
                    Path(self.init['targetdir_mp4']).as_posix()
                ])
            self.precent = 100
            try:
                novoice_mp4_path.unlink(missing_ok=True)
                hard_srt_path.unlink(missing_ok=True)
                Path(mp4_dirpath.as_posix() + "/tmp.srt.ass").unlink(missing_ok=True)
            except Exception:
                pass
            return True
        # 需要配音但没有配音文件
        if self.config_params['voice_role'] != 'No' and not tools.vail_file(self.init['target_wav']):
            raise Exception(f"{config.transobj['Dubbing']}{config.transobj['anerror']}:{self.init['target_wav']}")

        # 需要双字幕
        if len(target_sub_list)>0 and len(source_sub_list) > 0:
            # 处理双硬字幕
            if self.config_params['subtitle_type'] == 3:
                text = ""
                source_length = len(source_sub_list)
                for i, it in enumerate(target_sub_list):
                    it['text'] = textwrap.fill(it['text'], maxlen, replace_whitespace=False).replace('\n', '\\N')
                    text += f"{it['line']}\n{it['time']}\n{it['text'].strip()}"
                    if source_length > 0 and i < source_length:
                        text += "\\N" + textwrap.fill(source_sub_list[i]['text'], maxlen_source,
                                                      replace_whitespace=False).replace('\n', '\\N').strip()
                    text += "\n\n"
                hard_srt_path.write_text(text.strip(), encoding="utf-8", errors="ignore")
                os.chdir(mp4_dirpath)
                shutil.copy2(hard_srt_path.as_posix(), f"{self.obj['output']}/shuang.srt")
                hard_srt = tools.set_ass_font(hard_srt_path.as_posix())

            # 双字幕 软字幕
            elif self.config_params['subtitle_type'] == 4:
                text = ""
                for i, it in enumerate(target_sub_list):
                    text += f"{it['line']}\n{it['time']}\n{it['text'].strip()}"
                    if i < len(source_sub_list):
                        text += f"\n{source_sub_list[i]['text'].strip()}"
                    text += "\n\n"
                # 软字幕双
                soft_srt = self.obj['linshi_output'] + "/shuang.srt"
                shutil.copy2(self.init['target_sub'], soft_srt)
                with open(soft_srt, 'w', encoding="utf-8", errors="ignore") as f:
                    f.write(text.strip())
                soft_srt = Path(soft_srt).as_posix()

        # 分离背景音和添加背景音乐
        self._back_music()
        self._separate()
        # 有配音 延长视频或音频对齐
        if self.config_params['voice_role'] != 'No' and self.config_params['append_video']:
            video_time = tools.get_video_duration(novoice_mp4)
            try:
                audio_length = int(tools.get_audio_time(self.init['target_wav']) * 1000)
            except Exception:
                audio_length = 0
            if audio_length > 0 and audio_length > video_time:
                try:
                    # 先对音频末尾移除静音
                    tools.remove_silence_from_end(self.init['target_wav'], is_start=False)
                    audio_length = int(tools.get_audio_time(self.init['target_wav']) * 1000)
                except Exception:
                    audio_length = 0
            if audio_length > 0 and audio_length > video_time:
                # 视频末尾延长
                try:
                    # 对视频末尾定格延长
                    self._novoicemp4_add_time(audio_length - video_time)
                except Exception as e:
                    print(f'{config.transobj["moweiyanchangshibai"]}:{str(e)}')
                    config.logger.error(f'视频末尾延长失败:{str(e)}')
            elif audio_length > 0 and video_time > audio_length:
                ext = self.init['target_wav'].split('.')[-1]
                m = AudioSegment.from_file(
                    self.init['target_wav'],
                    format="mp4" if ext == 'm4a' else ext) + AudioSegment.silent(
                    duration=video_time - audio_length)
                m.export(self.init['target_wav'], format="mp4" if ext == 'm4a' else ext)
        try:
            subtitle_language = translator.get_subtitle_code(show_target=self.config_params['target_language'])
            # 有配音有字幕
            if self.config_params['voice_role'] != 'No' and self.config_params['subtitle_type'] > 0:
                if self.config_params['subtitle_type'] in [1, 3]:
                    tools.set_process(config.transobj['peiyin-yingzimu'], btnkey=self.init['btnkey'])
                    # 需要配音+硬字幕
                    tools.runffmpeg([
                        "-y",
                        "-i",
                        novoice_mp4,
                        "-i",
                        Path(self.init['target_wav']).as_posix(),
                        "-c:v",
                        f"libx{self.video_codec}",
                        "-c:a",
                        "aac",
                        "-vf",
                        f"subtitles={hard_srt}",
                        '-crf',
                        f'{config.settings["crf"]}',
                        '-preset',
                        config.settings['preset'],
                        Path(self.init['targetdir_mp4']).as_posix()
                    ])
                else:
                    tools.set_process(config.transobj['peiyin-ruanzimu'], btnkey=self.init['btnkey'])
                    # 配音+软字幕
                    tools.runffmpeg([
                        "-y",
                        "-i",
                        novoice_mp4,
                        "-i",
                        Path(self.init['target_wav']).as_posix(),
                        "-i",
                        soft_srt,
                        "-c:v",
                        "copy",
                        "-c:a",
                        "aac",
                        "-c:s",
                        "mov_text",
                        "-metadata:s:s:0",
                        f"language={subtitle_language}",
                        Path(self.init['targetdir_mp4']).as_posix()
                    ])
            elif self.config_params['voice_role'] != 'No':
                # 有配音无字幕
                tools.set_process(config.transobj['onlypeiyin'], btnkey=self.init['btnkey'])
                tools.runffmpeg([
                    "-y",
                    "-i",
                    novoice_mp4,
                    "-i",
                    Path(self.init['target_wav']).as_posix(),
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    Path(self.init['targetdir_mp4']).as_posix()
                ])
            # 硬字幕无配音  原始 wav合并
            elif self.config_params['subtitle_type'] in [1, 3]:
                tools.set_process(config.transobj['onlyyingzimu'], btnkey=self.init['btnkey'])
                cmd = [
                    "-y",
                    "-i",
                    novoice_mp4
                ]
                if tools.vail_file(self.init['source_wav']):
                    cmd.append('-i')
                    cmd.append(Path(self.init['source_wav']).as_posix())

                cmd.append('-c:v')
                cmd.append(f'libx{self.video_codec}')
                if tools.vail_file(self.init['source_wav']):
                    cmd.append('-c:a')
                    cmd.append('aac')
                cmd += [
                    "-vf",
                    f"subtitles={hard_srt}",
                    '-crf',
                    f'{config.settings["crf"]}',
                    '-preset',
                    config.settings['preset'],
                    Path(self.init['targetdir_mp4']).as_posix(),
                ]
                tools.runffmpeg(cmd)
            elif self.config_params['subtitle_type'] in [2, 4]:
                # 软字幕无配音
                tools.set_process(config.transobj['onlyruanzimu'], btnkey=self.init['btnkey'])
                # 原视频
                cmd = [
                    "-y",
                    "-i",
                    novoice_mp4
                ]
                # 原配音流
                if tools.vail_file(self.init['source_wav']):
                    cmd.append("-i")
                    cmd.append(Path(self.init['source_wav']).as_posix())
                # 目标字幕流
                cmd += [
                    "-i",
                    soft_srt,
                    "-c:v",
                    "copy"
                ]
                if tools.vail_file(self.init['source_wav']):
                    cmd.append('-c:a')
                    cmd.append('aac')
                cmd += [
                    "-c:s",
                    "mov_text",
                    "-metadata:s:s:0",
                    f"language={subtitle_language}",
                    '-crf',
                    f'{config.settings["crf"]}',
                    '-preset',
                    config.settings['preset']
                ]
                cmd.append(Path(self.init['targetdir_mp4']).as_posix())
                tools.runffmpeg(cmd)
        except Exception as e:
            raise Exception(f'compose srt + video + audio:{str(e)}')
        self.precent = 99
        try:

            if not self.config_params['only_video']:
                with open(self.init['target_dir'] + f'/{"readme" if config.defaulelang != "zh" else "文件说明"}.txt',
                          'w', encoding="utf-8", errors="ignore") as f:
                    f.write(f"""以下是可能生成的全部文件, 根据执行时配置的选项不同, 某些文件可能不会生成, 之所以生成这些文件和素材，是为了方便有需要的用户, 进一步使用其他软件进行处理, 而不必再进行语音导出、音视频分离、字幕识别等重复工作


{os.path.basename(self.init['targetdir_mp4'])} = 最终完成的目标视频文件
{self.init['source_language_code']}.m4a|.wav = 原始视频中的音频文件(包含所有背景音和人声)
{self.init['target_language_code']}.m4a = 配音后的音频文件(若选择了保留背景音乐则已混入)
{self.init['source_language_code']}.srt = 原始视频中根据声音识别出的字幕文件
{self.init['target_language_code']}.srt = 翻译为目标语言后字幕文件
shuang.srt = 双语字幕
vocal.wav = 原始视频中分离出的人声音频文件
instrument.wav = 原始视频中分离出的背景音乐音频文件


如果觉得该项目对你有价值，并希望该项目能一直稳定持续维护，欢迎各位小额赞助，有了一定资金支持，我将能够持续投入更多时间和精力
捐助地址：https://github.com/jianchang512/pyvideotrans/issues/80

====

Here are the descriptions of all possible files that might exist. Depending on the configuration options when executing, some files may not be generated.

{os.path.basename(self.init['targetdir_mp4'])} = The final completed target video file
{self.init['source_language_code']}.m4a|.wav = The audio file in the original video (containing all sounds)
{self.init['target_language_code']}.m4a = The dubbed audio file (if you choose to keep the background music, it is already mixed in)
{self.init['source_language_code']}.srt = Subtitles recognized in the original video
{self.init['target_language_code']}.srt = Subtitles translated into the target language
shuang.srt = Source language and target language subtitles srt 
vocal.wav = The vocal audio file separated from the original video
instrument.wav = The background music audio file separated from the original video


If you feel that this project is valuable to you and hope that it can be maintained consistently, we welcome small sponsorships. With some financial support, I will be able to continue to invest more time and energy
Donation address: https://ko-fi.com/jianchang512


====

Github: https://github.com/jianchang512/pyvideotrans
Docs: https://pyvideotrans.com

                """)

            novoice_mp4_path.unlink(missing_ok=True)
            hard_srt_path.unlink(missing_ok=True)
            Path(mp4_dirpath.as_posix() + "/tmp.srt.ass").unlink(missing_ok=True)
        except:
            pass
        self.precent = 100
        return True
