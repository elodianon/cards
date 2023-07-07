" Vim syntax file
" Language:         .card AI chatbot file

if exists("b:current_syntax")
    finish
endif

" Keys
syn match dcrdKeyMark /^\s*@/ nextgroup=dcrdBadKeyBlock,dcrdKeyBlock
syn region dcrdBadKeyBlock start=/\(modified\|tool\|alternate_greetings\)\( \|$\)/ end=/^\s*@/me=s-1 contained
syn region dcrdKeyBlock matchgroup=dcrdUnknownKey start=/[A-Za-z_]\++\?\( \|$\)/ end=/^\s*@/me=s-1 contained
syn region dcrdKeyBlock matchgroup=dcrdKey start=/\(name\|creator_notes\|creator\|character_version\|extensions\)\( \|$\)/ end=/^\s*@/me=s-1 contained
syn region dcrdKeyBlock matchgroup=dcrdKey start=/tags\( \|$\)/ end=/^\s*@/me=s-1 contained contains=dcrdItemSeparator
syn region dcrdKeyBlock matchgroup=dcrdKey start=/\(first_mes\|personality\|scenario\|alternate_greetings+\)\( \|$\)/ end=/^\s*@/me=s-1 contained contains=@dcrdText,dcrdPlaceholder
syn region dcrdKeyBlock matchgroup=dcrdKey start=/mes_example\( \|$\)/ end=/^\s*@/me=s-1 contained contains=@dcrdText,dcrdPlaceholder,dcrdExampleKeyword
syn region dcrdKeyBlock matchgroup=dcrdKey start=/\(system_prompt\|post_history_instructions\)\( \|$\)/ end=/^\s*@/me=s-1 contained contains=@dcrdText,dcrdPlaceholder,dcrdPromptPlaceholder

" Character book
syn region dcrdKeyBlock matchgroup=dcrdKey start=/character_book\( \|$\)/ end=/^\s*@/me=s-1 contained contains=dcrdBookKeyMark
syn match dcrdBookKeyMark /^\s*|/ nextgroup=dcrdBookKeyBlock contained
syn region dcrdBookKeyBlock matchgroup=dcrdUnknownKey start=/[A-Za-z_]\++\?\( \|$\)/             end=/^\s*|/me=s-1 end=/^\s*@/me=s-1 contained
syn region dcrdBookKeyBlock matchgroup=dcrdKey start=/\(name\|description\|extensions\)\( \|$\)/ end=/^\s*|/me=s-1 end=/^\s*@/me=s-1 contained
syn region dcrdBookKeyBlock matchgroup=dcrdKey start=/\(scan_depth\|token_budget\)\( \|$\)/      end=/^\s*|/me=s-1 end=/^\s*@/me=s-1 contained contains=@dcrdInt
syn region dcrdBookKeyBlock matchgroup=dcrdKey start=/recursive_scanning\( \|$\)/                end=/^\s*|/me=s-1 end=/^\s*@/me=s-1 contained contains=@dcrdBool

" Character book entry
syn region dcrdKeyBlock matchgroup=dcrdKey start=/entries+\( \|$\)/ end=/^\n*\s*@/me=s-1 fold contained contains=dcrdBookEntryKeyMark
syn match dcrdBookEntryKeyMark /^\s*|/ nextgroup=dcrdBookEntryKeyBlock contained
syn region dcrdBookEntryKeyBlock matchgroup=dcrdUnknownKey start=/[A-Za-z_]\++\?\( \|$\)/                             end=/^\s*|/me=s-1 end=/^\n*\s*@/me=s-1 contained
syn region dcrdBookEntryKeyBlock matchgroup=dcrdKey start=/\(name\|extensions\|comment\)\( \|$\)/                     end=/^\s*|/me=s-1 end=/^\n*\s*@/me=s-1 contained
syn region dcrdBookEntryKeyBlock matchgroup=dcrdKey start=/\(keys\|secondary_keys\)\( \|$\)/                          end=/^\s*|/me=s-1 end=/^\n*\s*@/me=s-1 contained contains=dcrdItemSeparator
syn region dcrdBookEntryKeyBlock matchgroup=dcrdKey start=/\(insertion_order\|priority\|id\)\( \|$\)/                 end=/^\s*|/me=s-1 end=/^\n*\s*@/me=s-1 contained contains=@dcrdInt
syn region dcrdBookEntryKeyBlock matchgroup=dcrdKey start=/\(selective\|constant\|enabled\|case_sensitive\)\( \|$\)/  end=/^\s*|/me=s-1 end=/^\n*\s*@/me=s-1 contained contains=@dcrdBool
syn region dcrdBookEntryKeyBlock matchgroup=dcrdKey start=/position\( \|$\)/                                          end=/^\s*|/me=s-1 end=/^\n*\s*@/me=s-1 contained contains=@dcrdPosition

" Content
syn region dcrdKeyBlock matchgroup=dcrdKey start=/description\( \|$\)/ end=/\s*<!>\s*/me=s-1 end=/^\s*@/me=s-1 contained contains=@dcrdDef nextgroup=dcrdDescriptionBlockB
syn region dcrdDescriptionBlockA start=/\s*<!>\s*/hs=e+1 end=/\s*<!>\s*/me=s-1 end=/^\s*@/me=s-1 contained contains=@dcrdDef,dcrdMinSeparator nextgroup=dcrdDescriptionBlockB
syn region dcrdDescriptionBlockB start=/\s*<!>\s*/hs=e+1 end=/\s*<!>\s*/me=s-1 end=/^\s*@/me=s-1 contained contains=@dcrdText,dcrdPlaceholder,dcrdMinSeparator nextgroup=dcrdDescriptionBlockA

syn region dcrdBookEntryKeyBlock matchgroup=dcrdKey start=/content\( \|$\)/ end=/\s*<!>\s*/me=s-1 end=/^\s*|/me=s-1 end=/^\n*\s*@/me=s-1 contained contains=@dcrdDef nextgroup=dcrdEntryContentBlockB
syn region dcrdEntryContentBlockA start=/\s*<!>\s*/hs=e+1 end=/\s*<!>\s*/me=s-1 end=/^\s*|/me=s-1 end=/^\s*@/me=s-1 contained contains=@dcrdDef,dcrdMinSeparator nextgroup=dcrdEntryContentBlockB
syn region dcrdEntryContentBlockB start=/\s*<!>\s*/hs=e+1 end=/\s*<!>\s*/me=s-1 end=/^\s*|/me=s-1 end=/^\s*@/me=s-1 contained contains=@dcrdText,dcrdPlaceholder,dcrdMinSeparator nextgroup=dcrdEntryContentBlockA

syn match dcrdMinSeparator /\s*<!>\s*/ contained
syn region dcrdDefBlock matchgroup=dcrdDefBraces start=/{/ end=/}/ fold contained contains=@dcrdDef
syn match dcrdDefEnd /;/ contained
syn cluster dcrdDef contains=dcrdPlaceholder,dcrdDefBlock,dcrdDefEnd

" Values
syn match dcrdExampleKeyword /\c<START>/ contained
syn match dcrdItemSeparator /,/ contained

syn match dcrdInvalid /.*/ contained
syn match dcrdPositionValid /\c\<\(before_char\|after_char\)\>/ contained
syn cluster dcrdPosition contains=dcrdPositionValid,dcrdInvalid
syn match dcrdIntValid /\<[-+]\?\d\+\>/ contained
syn cluster dcrdInt contains=dcrdIntValid,dcrdInvalid
syn match dcrdBoolValid /\c\<\(true\|false\)\>/ contained
syn cluster dcrdBool contains=dcrdBoolValid,dcrdInvalid

" Placeholders
syn match dcrdPlaceholder /\c\({{\(char\|user\)}}\|<\(BOT\|USER\)>\)/ contained
syn match dcrdPromptPlaceholder /\c{{original}}/ contained

" Text
"syn region dcrdItalic start=/\*/ end=/\*/ contained
"syn region dcrdBold start=/\*\*/ end=/\*\*/ contained
"syn cluster dcrdText contains=dcrdBold,dcrdItalic,@dcrdText

" Global
syn match dcrdError /^\s*@\s*$/ containedin=ALL
syn match dcrdComment "^\s*#.*$" containedin=ALLBUT,dcrdBadKeyBlock
syn match dcrdConst "^\s*\$.*$" containedin=ALLBUT,dcrdBadKeyBlock
syn match dcrdConstReplace /\c{{$[A-Za-z]\+[A-Za-z_0-9]*}}/ containedin=ALLBUT,dcrdBadKeyBlock

let b:current_syntax = "dotcard"

syn sync fromstart

hi def link dcrdKeyMark Delimiter
hi def link dcrdBookKeyMark Delimiter
hi def link dcrdBookEntryKeyMark Delimiter

hi def link dcrdUnknownKey Function
hi def link dcrdBadKeyBlock Error
hi def link dcrdKey Keyword

hi def link dcrdMinSeparator Keyword
hi def link dcrdDefBraces Delimiter
hi def link dcrdDefEnd Delimiter
hi def link dcrdItemSeparator Delimiter

hi def link dcrdExampleKeyword Constant
hi def link dcrdPlaceholder Constant
hi def link dcrdPromptPlaceholder Constant

hi def link dcrdInvalid Error
hi def link dcrdPositionValid Constant
hi def link dcrdIntValid String
hi def link dcrdBoolValid Constant

hi def link dcrdError Error
hi def link dcrdComment Comment
hi def link dcrdConst Delimiter
hi def link dcrdConstReplace Delimiter

"hi dcrdBold cterm=bold gui=bold
"hi dcrdItalic cterm=italic gui=italic
