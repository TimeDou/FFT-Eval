"""Export the three requested visible conversations, with source provenance."""
from pathlib import Path
from datetime import datetime
import collections
import hashlib
import json
import re

BASE=Path('/mnt/DATA1/sj/ALS/DP2.0')
SOURCES={
 'Claude-DS-Flash':Path('/mnt/DATA1/sj/.claude/projects/-mnt-DATA1-sj-FFT-Claude-DS-Flash/dd9b3f1d-5e5f-435b-838f-1a77ee51b71a.jsonl'),
 'Codex-GPT-6.1-Sol-Max':Path('/mnt/DATA1/sj/.codex/sessions/2026/11/22/rollout-2026-11-22T18-45-17-01a202dc-3c29-75e3-b52b-bbef0354e225.jsonl'),
 'Codex-GPT-6.2-Sol-Max':Path('/mnt/DATA1/sj/.codex/sessions/2026/11/22/rollout-2026-11-22T18-45-31-01a202dc-732f-72b1-9dc8-784c938afa81.jsonl'),
}
DURATIONS={'Claude-DS-Flash':('1h55m16s',6916),'Codex-GPT-6.1-Sol-Max':('37m33s',2253),
           'Codex-GPT-6.2-Sol-Max':('37m15s',2235)}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def elapsed(start,end):
    return (datetime.fromisoformat(end.replace('Z','+00:00'))-
            datetime.fromisoformat(start.replace('Z','+00:00'))).total_seconds()


def visible_content(items,omissions):
    if isinstance(items,str):
        return items
    result=[]
    for item in items:
        if isinstance(item,dict)and item.get('type')in{'thinking','redacted_thinking','reasoning','analysis'}:
            omissions['private_reasoning_blocks']+=1
            continue
        result.append(item)
    return result


def codex(records):
    events=[];omissions=collections.Counter();models=set();first=None;last=None;prompt=None;usage=None;timing={}
    metadata={}
    for i,r in enumerate(records):
        typ=r.get('type');p=r.get('payload',{});stamp=r.get('timestamp')
        if typ=='session_meta':
            metadata={k:p.get(k)for k in ['id','cwd','source','originator','cli_version','model_provider']}
        elif typ=='turn_context':
            models.add((p.get('model'),p.get('effort',p.get('reasoning_effort'))))
        elif typ=='event_msg'and p.get('type')=='user_message'and first is None:
            first=stamp;prompt=p.get('message','')
        elif typ=='event_msg'and p.get('type')=='token_count':
            usage=p.get('info')
        elif typ=='event_msg'and p.get('type')=='task_started':
            timing['engine_task_started_utc']=stamp
        elif typ=='event_msg'and p.get('type')=='task_complete':
            timing['engine_task_completed_utc']=stamp
            timing['engine_task_duration_seconds']=p.get('duration_ms',0)/1000
        elif typ=='response_item':
            item=p.get('type')
            if item=='message':
                if p.get('role')not in{'user','assistant'}or p.get('channel')=='analysis' or p.get('phase')=='analysis':
                    omissions['internal_context_or_analysis_messages']+=1;continue
                q={k:v for k,v in p.items()if not k.startswith('internal_')}
                q['content']=visible_content(q.get('content',[]),omissions)
                events.append(dict(timestamp=stamp,source_record_index=i,event=q))
                if p.get('role')=='assistant'and p.get('phase')=='final_answer':last=stamp
            elif item in {'function_call','function_call_output','custom_tool_call','custom_tool_call_output'}:
                events.append(dict(timestamp=stamp,source_record_index=i,event={k:v for k,v in p.items()if not k.startswith('internal_')}))
            elif item=='reasoning':
                omissions['private_reasoning_events']+=1
            else:
                omissions['internal_response_items']+=1
    assert first and last and prompt
    return events,dict(session=metadata,models=[dict(model=m,effort=e)for m,e in sorted(models)],
        task_start_utc=first,final_visible_answer_utc=last,
        logged_task_wall_seconds=elapsed(first,last),logged_token_usage=usage,**timing),prompt,omissions


def claude(records):
    starts=[i for i,r in enumerate(records)if r.get('type')=='user'and isinstance(r.get('message',{}).get('content'),str)
            and r['message']['content'].startswith('# FFT64-Quant:')]
    assert len(starts)==1
    start=starts[0];first=records[start]['timestamp'];prompt=records[start]['message']['content']
    events=[];omissions=collections.Counter();models=set();last=None;usage=[]
    for i,r in enumerate(records):
        if i<start:
            omissions['pre_task_setup_records']+=1;continue
        typ=r.get('type');message=r.get('message',{})
        if typ not in {'user','assistant'}or not isinstance(message,dict):
            omissions['non_conversation_records']+=1;continue
        if r.get('isMeta'):
            omissions['internal_context_records']+=1;continue
        content=visible_content(message.get('content',[]),omissions)
        if isinstance(content,str)and content.startswith(('<command-name>','<local-command-stdout>')):
            omissions['local_commands_outside_task']+=1;continue
        if not content:
            continue
        item=dict(type='message',role=typ,content=content)
        for key in ['model','usage','stop_reason','id']:
            if key in message:item[key]=message[key]
        events.append(dict(timestamp=r.get('timestamp'),source_record_index=i,uuid=r.get('uuid'),
                           parent_uuid=r.get('parentUuid'),event=item))
        if typ=='assistant':
            if message.get('model'):models.add(message['model'])
            if message.get('usage'):usage.append(message['usage'])
            if any(isinstance(x,dict)and x.get('type')=='text'and x.get('text')for x in content):
                last=r.get('timestamp')
    assert first and last and prompt
    # Trailing local exit commands can be much later than the actual answer.
    events=[r for r in events if r.get('timestamp')and r['timestamp']<=last]
    return events,dict(models=[dict(model=m)for m in sorted(models)],task_start_utc=first,
        final_visible_answer_utc=last,logged_task_wall_seconds=elapsed(first,last),
        assistant_usage_records=usage,
        exclusion_note='Earlier local /clear and /model setup and later /exit idle time are not task duration'),prompt,omissions


def redact_credentials(value,counts):
    if isinstance(value,list):return [redact_credentials(x,counts)for x in value]
    if isinstance(value,dict):return {k:redact_credentials(v,counts)for k,v in value.items()}
    if not isinstance(value,str):return value
    patterns=[r'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}\b',
              r'\b(?:ghp|github_pat)_[A-Za-z0-9_]{24,}\b',r'\bAIza[0-9A-Za-z_-]{30,}\b']
    for pattern in patterns:
        value,n=re.subn(pattern,'[REDACTED_CREDENTIAL]',value);counts['credential_like_tokens']+=n
    return value


def main():
    root=Path('/tmp/fft_final_agent_review_path.txt').read_text().strip();root=Path(root)
    summaries=[]
    for name,source in SOURCES.items():
        raw=source.read_bytes();records=[json.loads(line)for line in raw.decode().splitlines()if line.strip()]
        events,metadata,prompt,omissions=claude(records)if name=='Claude-DS-Flash'else codex(records)
        duration,seconds=DURATIONS[name]
        canonical=re.sub(r'[\s\\]+','',prompt)
        provenance=dict(agent=name,source_file=str(source),source_sha256=sha(raw),source_bytes=len(raw),
            source_record_count=len(records),export_event_count=len(events),
            user_reported_duration=duration,user_reported_duration_seconds=seconds,
            duration_source='user_reported conversation wall time; independent verification runtime recorded separately',
            prompt_sha256=sha(prompt.encode()),prompt_whitespace_escape_normalized_sha256=sha(canonical.encode()),
            omissions=dict(omissions),**metadata)
        if 'engine_task_duration_seconds'in metadata:
            provenance['engine_duration_minus_user_reported_seconds']=metadata['engine_task_duration_seconds']-seconds
        record=dict(schema='visible_conversation_with_tools',provenance=provenance,events=events,
            export_scope='User/assistant visible messages and tool calls/results. Private reasoning, system/developer context, provider request blobs and encrypted reasoning are not exported.')
        counts=collections.Counter();record=redact_credentials(record,counts)
        record['provenance']['redactions']=dict(counts)
        destination=root/'conversations'/name;destination.mkdir(parents=True,exist_ok=True)
        data=(json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode()
        (destination/'conversation.json').write_bytes(data)
        (destination/'metadata.json').write_text(json.dumps(dict(record['provenance'],export_sha256=sha(data)),ensure_ascii=False,indent=2)+'\n')
        (destination/'initial_prompt.txt').write_text(prompt)
        summaries.append(dict(agent=name,user_reported_duration=duration,user_reported_seconds=seconds,
            logged_seconds=metadata['logged_task_wall_seconds'],source_sha256=sha(raw),
            export_sha256=sha(data),export_bytes=len(data),visible_events=len(events),
            models=metadata['models'],prompt_normalized_sha256=sha(canonical.encode()),redactions=dict(counts)))
    (root/'conversation_summary.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2)+'\n')
    for item in summaries:
        print(json.dumps(item,ensure_ascii=False))


if __name__=='__main__':main()
