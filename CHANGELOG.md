# Changelog

## 2026-10-31

- A graded quiz page leaves its result on the book in memory: `props["results"]`, one `{page, choice, right}` per page, the last answer winning. A ToolBook file is never graded here, so it records nothing. Foolcourse does not see it yet. Tested in `engine/test_choice_score.py`.
- A graded quiz answer goes to the quiz's `next` page when right and its `again` page when wrong, unless the button has a script of its own. The window does this only for a button that has `choice`, so the A–E path is unchanged. Tested in `engine/test_choice_next.py`.
- A graded quiz answer shows the shape marked `feedback: "right"` or `feedback: "wrong"` for its result and hides the other. Only a Foolbook book is graded, so no ToolBook page changes. Tested in `engine/test_choice_feedback.py`.
- In a book of Foolbook's own format, a quiz answer button is graded by its `choice` index into `page.quiz.choices`, not by its name, and the answer is kept in `__answer`. Only a button that has `choice` is graded, and a ToolBook file never is, so the A–E `handleQuizClick` path is unchanged. Tested in `engine/test_choice_grade.py`.
- `engine.subset.check(script)` (and `foolbook.core.check_script`) parses a script in the subset and returns errors with line numbers: an open quote, an open or doubly closed block, `else` outside an `if` or `conditions`, `go to` with no page, `if` with no condition. It reads ToolBook's own forms (`end buttonClick`, `notifyAfter idle`, `while`, `linkDLL32`, `go to` an expression, a stored handler body ending `end enterPage`, a quote that runs onto the next line, a handler closed by the end of its script), and every script in 93950101 checks clean. It is a check, not a compile. Tested in `engine/test_check.py`.
- In a ToolBook file, `go to next page` and `go to previous page` (also `prev`, and `of this book`) go to the page beside this one in book order, through `goto`, so leavePage runs. Before, they were notes and did nothing. A book in Foolbook's own format does not read them; it has `send next` and `send previous`. The converted NIDA courses are FBK1 files, so they are unchanged. Tested in `engine/test_go_next_page.py`.
- quiz_check finds a `goto` page again. The viewer's page list shows every page id only in developer mode, so a spec's `goto` found no page. quiz_check now opens the developer page list, without `--debug` and the decoded files it writes beside the book. Tested in `tools/quiz_check/test_child_page_ids.py`.
- `show "Name"`, `hide "Name"`, and `show shape "Name"` act on every shape of that name on the page, or `of page "P"`, whatever its kind. This is for books in Foolbook's own format, so a hotspot or text shape can be shown without a ToolBook class word. A ToolBook file does not get this reading. Tested in `engine/test_show_hide_name.py`.
- A `go to` in a page's leavePage is where the reader lands. Before, `goto` ran leavePage and dropped its `go to`. No leavePage in the NIDA books checked goes anywhere, so NIDA pages land where they did. Tested in `engine/test_page_leave.py`.
- An `.fbk` page script with no `to handle` line runs when the page is shown, as the page's `enterPage`. Before, it was loaded as a handler named `script` and never ran. Tested in `engine/test_page_enter.py`.
- A `.fbk` book can store `author` and `firstPage`. The reader opens at the first page id when that page exists, else at the first page, and so does a book opened with Open. A saved last page the student picks still wins, and a ToolBook book, which has no first page id, still opens on page 0. `engine/test_first_page.py`.
- `foolbook.core.unknown_words(script)` gives FoolbookEditor the interpreter's answer through the core, so the editor does not import the engine. Tested in `engine/test_core_unknown_words.py`.
- In a book of Foolbook's own format, a button script with no `to handle` line is the click. Before, it was not run. A ToolBook file does not get this reading (`engine.origin.is_toolbook`). No button in the converted NIDA courses has such a script, so their clicks are unchanged. `engine.engine.click` runs a click in the window's order without a window. Tested in `engine/test_click_order.py`.
- A `roundrect` shape is drawn with rounded corners from its bounds and `radius` (8 when missing). It was a square box.
- A shape's `stroke` is the width of its outline or line, in pixels, scaled with the page. Rect, roundrect, ellipse, line, polygon, and arc honor it. A shape with no `stroke` is drawn as before.
- A `curve` shape is drawn as a polyline through its `points`. It was a box at its bounds. knownbugs.md says it is not smoothed yet.
- An `arc` that stores `start` and `sweep` is drawn as that part of the ellipse in its bounds, unfilled. An arc read from a `.tbk` (endpoints or rays) is drawn as before.
- A `pie` shape is drawn as a filled slice of the ellipse in its bounds, from `start` and `sweep`. It was a box.
- A `chord` shape is drawn as the slice of the ellipse between `start` and `sweep`, closed by a straight line and filled. It was a box.
- A `hotspot` shape is not drawn. A click inside it is the hotspot, and its `item` is followed like a button's. It was drawn as a box with an outline.
- An `.fbk` text shape with `underline` is drawn underlined. Before, only face, size, bold, and italic were read.
- An `.fbk` text shape may name its alignment: `left`, `center`, or `right`. A wrapped field is justified the same way. A named alignment used to stop the page from drawing, because only the `.tbk` number was read.
- `engine.subset.unknown_words(script)` names each line the interpreter does not act on, with its line number, by running the line through the interpreter on an empty book. Nothing is typed twice, so the warning cannot drift from what runs. FoolbookEditor warns from it. `MESSAGES` lists the `send` messages that move the reader. Tested in `engine/test_subset.py`.
- `engine.origin.is_toolbook(book)` says whether a book's file is a ToolBook file, from its first bytes (`toolbook.format.is_toolbook`) or a TBKX, not from its name. An FBK1 envelope is Foolbook whatever it is called. Behavior that differs between the two asks here. Nothing calls it yet. Tested in `engine/test_origin.py`.

## Unreleased

- `SendMessageA` and `PostMessageA` linked from user32.dll answer 0 and are kept in `__windowMessages`. The reader gives a script no window handle of its own, so the handle is another program's window (nc81base sends to the records window NIDAREC.INI names), which the reader cannot reach. Tested in `engine/test_user32.py`.
- `fileExists32(name)` linked from tbfile32.dll gives 1 when the file is beside the book, whatever its case, and 0 when not. Tested in `engine/test_tbfile32.py`.
- `GetTickCount()` linked from kernel32.dll gives milliseconds as Windows does, so a script can time itself. Tested in `engine/test_linked_dll.py`.
- A `;` outside quotes ends a statement: `a = 1; b = 2` runs both, and `result = true;` sets true.
- `uppercase(x)` and `lowercase(x)` change the case of text.
- `get f()` leaves what f gives in `it`, so `return it` passes it on.
- A click's `target` is its object, `button "B" of page "P10210"`, so `object of target`, `name of target` and `enabled of target` work. `button temp` names an object by a variable.
- `increment(x)`, `decrement( x )` and `increment x by n` change the variable. Before, the bracket form did nothing and `by n` added 1.
- `ansiToChar(n)` gives the character with that ANSI code, and `charToAnsi(c)` the code of its first character.
- `pageNumber of this page`, `pageCount of this book`, and a property of another page by number or name, such as `questionno of page i`.
- A chunk of a variable can be set: `char i of pool = " "`, `item 2 of list = "x"`, `word 3 of s = "four"`. An item or textline past the end pads the list.
- `charCount`, `wordCount`, `itemCount` and `textlineCount` give how many of that chunk a value has.
- A handler parameter taken `by reference` binds to the caller's variable and writes back; an array passed by value is a copy.
- The openscript_analysis submodule moves to d741054, which has `formats/tbk/store.py`. Opening a ToolBook 8 object store and the Wingdings face test no longer fail on a missing module.
- `go to page(n)` goes to the nth page when n is a whole number and no page has that name, and `go to page(pages[3])` takes an array element.
- `random(n)` gives a whole number from 1 to n.
- `a is b` and `a is not b` compare like `=` and `<>` with a variable, number, flag, bare word or `null` on the right. `is not "x"` no longer reads as `is "x"`.
- An object can be named on another page or its background: `text of field("index") of parent of page i`, `set checked of button(temp) of page i to false`, `isObject(rectangle("correct") of page i)`. Text, visible, enabled and checked are read and set.
- Chunks of text: `word 2 of cmdLine`, `item i of pool`, `chars 2 to 4 of name` and `textline 3 of text of field "a"` give that part of the value. The index can be a sum or an array element, and past the end is empty.
- A bare `end` closes the block that is open, whatever kind it is. A `conditions` closed by `end` inside another `conditions`, or an `if` closed by `end` inside a `when`, no longer swallows the branches after it. nc81test's `gotoNextQuestionEx` closes its inner `conditions` this way.
- `while ... end while` and `do ... until` loop. `break while`, `break step`, `break do` and `break conditions` leave that block and the handler goes on, and `continue` starts the next pass. A handler with a `while` or `conditions` block inside it is no longer cut short at that block's own `end`.
- `linkDLL32 "kernel32.dll"` ... `end linkDLL32` declares DLL functions, `unlinkDLL` drops them, and `sysLinkedDLLs` lists the DLLs. A declared function with a shim in `engine/dlls/` answers. The first shim is kernel32's private profile calls: `GetPrivateProfileIntA` and `GetPrivateProfileStringA` read the INI beside the book and give the script's default when the key is not there, and `WritePrivateProfileStringA` keeps the value for the session without writing a file.
- `r is in "0,1,2"`, `"nc81base.sbk" is not in sysBooks` and `word contains "bc"` test for text inside text, ignoring case. A course's `if "nc81base.sbk" is not in sysBooks` guard now pushes its system books, so nc81base, nc81test, nc81recs and nc81trnr are open when its enterBook ends.
- `local int count`, `local string temp`, `local numbers[5]` and `local a, b` start each name blank when the line runs: 0 for a number type, empty otherwise, an empty array with brackets. A called handler counts from zero every time, and the caller's variable of the same name is left alone.
- Sums are worked out: `+`, `-`, `*`, `/`, `div` and `mod`, times before plus, left to right, brackets first, on variables, numbers, calls and array elements. `score div count` is a whole number. A side that is not a number still leaves the sum unknown, so nothing is written from it.
- A rectangle can carry `tile`, eight rows of eight bits, and it is filled with that pattern repeated: the outline colour for 1, the fill colour for 0. Each bit grows with the page scale.
- A `group` shape in an `.fbk` (what FoolbookEditor writes: `kind: group`, `children`) is replaced, for the reader, by its children in its place, so they are drawn in paint order and can be clicked. Before, the reader drew the group as one empty shape and lost its children. ToolBook pages, which name groups in `groups`, are passed through as before. Test: `engine/test_fbk_groups.py`.
- OpenScript arrays. `system int __menuFlags[10]` declares an array, `__menuFlags[index] = 2` sets an element, and `__menuFlags[3]` reads it. An element never set is 0 for a number type and empty for text. A system array keeps its elements when a called handler ends. A variable the reader already keeps in its own form is not written over.
- `send NAME args` runs the nearest `to handle NAME`: the page, the book, then each system book in `sysBooks` order. A `forward` goes on to the next one up, and a send no handler takes is left to the reader as before (`send next`). `send x to button "OK"` names its target and still takes the old path, and `send okClicked` still goes to the quiz until that family is retired.
- A call such as `x = getQuizScore()` or `get setMenuFlag(1)` runs the `to get` handler it reaches first: the page, the book, then each system book in `sysBooks` order. The built-in answers in `menu`, `fillin` and `quiz` are asked only when no handler is found. Arguments bind to the header's names, `return` gives the value, a `go to` inside goes to the line that called it, and only the handler's `system` variables keep what it did.
- `push "nc81base.sbk" onto sysBooks` opens that system book from beside the book, one folder up, or `core/`, and keeps it open with its handlers. The last push is first in `sysBooks`, and `sysBooks` reads as that list. A system book that is not found keeps its name. Calls do not reach its handlers yet.
- Deprecated and gone: the `foolbookeditor` package and the `author*` entry in `pyproject.toml`. The editor lives in [FoolbookEditor](https://github.com/squirelworks/FoolbookEditor), which owns `author` and `foolbookeditor`. Installing both no longer gives two packages of the same name. `python3 -m foolbookeditor` from FoolbookEditor is the editor. The shim here imported `author.gui`, which this repository no longer has.
- A page with `"background": true` is a shared background. It is not read as a page. A page that names it in `uses` paints its shapes first, then its own, so one edit shows on every page that uses it. A page whose shapes carry `layer: background` still paints as before. Test: `engine/test_backgrounds.py`.
- Objects the file stores as hidden are on the page, not shown: the TRY AGAIN! and CORRECT! boxes (a group stored hidden), a Response field a script shows, a mark or highlight rectangle. Before, the reader dropped the ones with their own hidden bit, and drew the members of a hidden group, so 93950404 P1720 opened with CORRECT! and TRY AGAIN! on top of each other. `send playAnimation to group "X"` ends with that group shown, so a hidden group an animation brings in is not lost. The reader depends on openscript_analysis#3 (commit 1466a94).
- `set visible of button "next" to true`, `show field "response"`, `hide rectangle "mark"` and `visible of button "x"` act on the object of that class and name, on this page or `of page "P"`. A Next the file stores hidden and a script shows (93950404 P1720 after the right answer) can now be shown.
- `getObjectiveScore(n)` is the average score of the questions of objective n, as nc81test.sbk adds them (`score div count`). Each question keeps its objective (`__quizTestNo`) when the pool is built by `addObjectiveToPool` or `addObjectiveToPoolEx`. P10410 (93951303) uses it to take the Review link off an objective that is already 100. The link itself goes with the group change (#17).
- `hide group`, `show group`, `set visible of group "X"`, `set visible of group("Review" && i)`, `if visible of group "X" is true` and `isObject(group "X")` act on the objects in that group. A page that hides groups on entry shows only what is left, and a Next that shows them first stays on the page. 93950605 P430: groups 2, 3 and 4 start hidden, Next shows them, a second Next goes to P440. 93950506 P2950 ends on group 4 as ToolBook's timed reveal does. The reader depends on openscript_analysis#2 (commit 7487267), which keeps the group names on each object.
- Return in a field of a multi-answer page moves the keyboard to the next field. `set focus to field "response 2"` in a field's keyUp handler gives that field the focus, and typing goes there. 93950102 P1090: type 0, Return, 5, Return, and so on down the four fields. The caret stays at the end of a field's text (`set caretLocation to 1,1` is not moved).
- Wrong fill-in answers are counted and right ones are scored. `IncorrectFillIn` counts the tries: the first two go to the try-again page (P2072), the third to the reveal page (P2073) and the count starts again. `saveEmbedded` scores 100 over the tries (100, 50, 33) and writes the response, and writes nothing unless `__studentRecords` is not 0. A wrong answer records nothing. The count is kept when the learner leaves a question, as in the book. nc81rec.dll is not there, so a record is kept in `__responses` with the fields the DLL is given.
- Return in an answer field runs the field's keyUp handler. It reads `text of field "Response"`, checks `ASYM_IsNumber`, compares (`response =7` and `response = "(3,5)"`, as numbers when both are numbers, ignoring case for text) and goes to the page the book names. 93950101 P2070: 7 goes to P2071, any other number to P2072, text that is not a number beeps and stays. The interpreter also reads `char N of x`, `testno of this page`, a compare with no spaces (`a =b`), a bracketed condition, `clear char N of x` and `beep`. `break` ends the handler it is in (it ended only the innermost `if`). `setupAndGoto(page)` goes to the page. Recording the answer and the count of tries are the next change.
- A page's `enterPage` clears its answer fields at reader level. `forward` runs the next handler at that line, the page's, then the background's, and the lines after it still run, so `get SetupFillInFields ()` is reached. 93950101 P2070 opens with an empty field, not the author's `?`. `SetupFillInFields` and `SetupFormFields` are read as nc81test.sbk writes them. `set textline N of text of field` sets one line, a value the reader cannot work out (a sum, an unknown call) is no longer written into a field, and `rgbfill of field "correct"` after a forward now un-highlights the answer.
- A field's own keyChar handler decides which keys go in. A numeric answer field takes `0-9 . + -` and Backspace and beeps on anything else. An alphabetic one takes A-Z in either case. A field with no keyChar handler takes every key. `DoNumeric` and `DoAlphabetic` are read as nc81test.sbk writes them, and `forward` is now recorded as an action.
- A click on an answer field gives it the keyboard. Typed characters and Backspace edit its text, and a caret shows where the next one goes. 93950101 P2070: click the field after `2 + 5 =`, type 7, and 7 is in the field. Return is taken by the field. What the field's own keyChar and keyUp scripts do with it is not run yet.

## 1.0.8r1 — 2026-10-25

- The reader depends on the openscript-analysis page-index fix (squirelworks/openscript_analysis#1, commit b5e6726). Every page table of a book is listed. 93950101 shows 301 pages, not 151, and P900 item 3 opens P3001. 9395B302 shows 423 pages, not 0. 93953402 and five other books open instead of showing "(unloadable)".
- The pin is a commit until that change is merged and tagged as 1.0.1r8.

## 1.0.8 — 2026-10-25

The 1.0.7 reader, released as 1.0.8.

- A book opens on the page in front of you. The other pictures stay in the file until that page is shown.
- The window opens large, and a resize is kept for the next course. A click redraws once.
- A jump uses the `.tbk` when a stub `.fsk` is sitting next to it. A settled export beside the original is what opens.
- `python3 -m foolbook --export` writes that export. The folder you name is done first. A short file is reported and the rest continue.
- The books a course names are opened in the background. `--freshstart` reinstalls 1.0.8.

## 1.0.7r23 — 2026-10-25

- A book opens without drawing every picture in it. The page on the screen is the one that is drawn. `?` was waiting on all of nida81.
- Another course named only as a number, such as 93954302.tbk, is not opened in the background.

## 1.0.7r22 — 2026-10-25

- The books a course names are opened in the background, up to three at a time, before a click asks for them. The terminal prints `opening` and the file.
- A settled export beside the .tbk or .sbk is what opens. A stub is not. The .tbk stays on disk.

## 1.0.7r21 — 2026-10-25

- `--export` of a folder does the files in that folder first, then the folders inside it. `courses/` was sorting ahead of the books sitting in the folder you named.
- A book that will not parse is reported and the rest continue. An `.fbk` or `.fsk` already written is left alone. `--force` writes it again.

## 1.0.7r20 — 2026-10-25

- A jump to nida81.tbk opens the .tbk when a .fsk or .fbk of that name is sitting next to it. The converted copy was the blank page.
- `python3 -m foolbook --export book.tbk` writes an .fbk beside the book with the pages, scripts, quiz properties, and pictures. An .sbk writes an .fsk. The original is left where it is.
- The window opens across most of the screen, and a resize is kept for the next course.
- A click redraws once, at the size already fitted.
- The titles in Using Foolbook and First Light stay on one line, in the colour they were given.

## 1.0.7r19 — 2026-10-25

- Begin on P10004 shows the raised face. Holding it shows the down face, and a chosen quiz letter shows its own checked face instead of a flat block.
- OK with nothing chosen beeps and stays. Skip does not advance on the first pass.
- A jump to a missing page stays on the lesson. The nida81 stub says the picture book is not beside the lesson, and shows the words it has.

## 1.0.7r18 — 2026-10-25

- The greeting keeps one face for the whole line, and the score line wraps inside its field.
- A coloured letter is pulled back to the ink before it when the book did not store a space there.
- White that touches the edge of an equipment picture is the page showing through. An unknown book property does not replace the version line.

## 1.0.7r17 — 2026-10-25

- A coloured letter is drawn once, at the width of the letters before it. A word that was fitted to its field keeps that size.
- The pale field behind a chip stays behind the pins and the number. P10 greets the student. The end of a test shows the score instead of XX.

## 1.0.7r16 — 2026-10-25

- A quiz letter is not coloured in before it is chosen. OK, Next, Skip and Back leave a question that was opened from the page list.
- The nida81 equipment picture is drawn. P310 is the computer.

## 1.0.7r15 — 2026-10-25

- The type is sized from the face Tk actually draws. Where that face is wider than Arial, the pixel size is divided back down. A label that is still wider than its field drops a pixel at a time until the word fits, instead of breaking in the middle.

## 1.0.7r14 — 2026-10-25

- Put the 96/72 type size back. The real viewer already matched ToolBook at every window size. r13 made it too small.

## 1.0.7r13 — 2026-10-25

- The type size is the point size times the window scale, not that times 96/72. The extra factor made the type a third too big at every window size.

## 1.0.7r12 — 2026-10-25

- The window opens at the size of the page, not the size of the monitor. A field stored past the page edge is cut there, so the P0 copyright no longer runs off.

## 1.0.7r11 — 2026-10-25

- A coloured letter is measured with the rest of its word, so it no longer sits on the next letter. The P2170 rows use the 10-point run, including the first letter of the header.

## 1.0.7r10 — 2026-10-25

- The menu labels change colour after the section is left. Flag 1 is P1910, flag 2 is P2910, and flag 10 is a quiz at 70 or better. The colour is hue 270, which is light purple. Exit stays black. The flags last for the session only.

## 1.0.7r9 — 2026-10-25

- The yellow letters on P1040 are painted on the same word, so they no longer open a gap or push "family" down a line. The P2170 table uses its 10-point run instead of the field's 12.

## 1.0.7r8 — 2026-10-25

- The highlighted letters on P1040 are drawn in the colour the run stores, which is yellow. The 16-colour guest is what made them look cyan.

## 1.0.7r7 — 2026-10-25

- A 12-point word is 16 pixels, which is what ToolBook draws. The window scale still multiplies that, and Tk is not allowed to do it again.
- An object's script stays on the object. An empty click no longer runs Next, and Lesson Exit asks once.
- A chosen answer turns the letter button light cyan. The words beside it are not framed.
- The reader now uses openscript-analysis 1.0.1r2, so the fields that had lost their font get it back.

## 1.0.7r6 — 2026-10-25

- Exit asks "Are you sure you want to Exit the Lesson?" The words are the book's own key handler. No stays. Yes leaves.
- On the score page, B goes to the menu only at 100. Any other score goes to P10410. A reviews the questions. OK with nothing chosen stays.

## 1.0.7r5 — 2026-10-25

- A click lands on the object under the pointer. An empty part of P300, P400, P450 or P900 stays there. P0 and P1 still go on, because that is their own script.
- "* Lesson Exit" is Arial 12. Only the star is the 8-point face.

## 1.0.7r4 — 2026-10-25

- The page fills the window again.
- Body text that lost its font was drawn at 12 points instead of the 12 pixels stored on the field. It uses the field's own font record.

## 1.0.7r3 — 2026-10-25

- A 12-point word is 12 pixels. The last change still drew it at 24-point size, and a large window stretched the page. The page now stays the size ToolBook uses.

## 1.0.7r2 — 2026-10-25

- A practice answer named `correct` stays on the page. Clicking it uses the fill the script names, then opens the CORRECT! page.
- An overlay page keeps the page under it and shows only its own corner label.

## 1.0.7r1 — 2026-10-25

- The face is sized in pixels, so it stays inside the field instead of growing past it.
- A quiz choice marks the letter that was clicked. OK moves to the next question. At the end, the percent replaces XX. A then OK opens the review, and B then OK returns to the menu.

## 1.0.7 — 2026-10-25

1.0.6 cleared the 1.0.5 revisions. This stays the version. A small change after it is `1.0.7r1`, then `r2`, and so on. A new version number waits for a real step.

- A book opened from the command line starts on the first page.
- A click on P0 or P1 runs the page's `send next`. The window was calling that handler without importing it, so the click did nothing.
- The type size and the indents scale with the window. A line that is wider than its box wraps. A short label that fits stays one line.

## 1.0.6 — 2026-10-25

This is the release. The `v1.0.5r1` through `v1.0.5r38` tags were interim builds. They are no longer published as releases.

What changed since 1.0.5, for a `.tbk`:

- The object store is what gets drawn. A page is its own list. A field's words are word 1 of the block at `+0x24`.
- The corner label is the page that is open, not the last page that wrote the field.
- A field is drawn in the face, point size, and weight the record names. The P400 body is Arial 12 bold. A style run can name a smaller face, which is why the copyright line is 8 point.
- The first indent word is the first line. The second is every line under it. The third is the right indent. The fourth is tab spacing and is not an inset. On the body those are 360, 360 and 310. On the P1 title the first line is 0 and the line under it is 650.
- A button picture is the bitmap stored in the book, drawn at the button's size. A transparent edge stays clear.
- A polygon is the outline in its own record, mapped onto its bounds. An arc is the open curve between its endpoints. A background fill is the colour stored on that record. A background with no fill leaves the page underneath where it does not paint.
- The window has one scale and one offset, applied before anything is drawn. The page is not shown until that scale is known.
- Next, Back, Menu, and the lesson choices run the script that was stored. A click on P0 or P1 sends next. A jump to another book leaves the first one open, and the return comes back to it.
- A text field named `correct` stays visible. That is the practice answer. The Correct rectangle, which is the answer key, stays hidden.
- Depends on `openscript_analysis` 1.0.1.

## 1.0.5r38

- The P1 title starts at the left of its box. Its first-line indent is 0. The 650 on the next word is only the line under it. Body text is unchanged, because those two words are both 360.

## 1.0.5r37

- Text is drawn in the face, point size, and weight stored on the field. The P400 body is Arial 12 bold. A style run can name a different entry, which is why the copyright line is 8 point.
- A text field named `correct` stays on the page. That is the answer on the practice questions. The Correct rectangle, which is the answer key, stays hidden.

## 1.0.5r36

- The right inset is the paragraph's right indent, not the left one. The tab spacing stays out of the picture. A field with no style runs is drawn in the face the record names. For the P400 body that face is Arial. Bold and 12-point are still not read.

## 1.0.5r35

- A field is drawn inside the margin words the record stored. A copyright inset of 720 twips is 48 pixels, and a body panel's 360 is 24.
- Saving a `.tbk` or `.sbk` writes an object store, not the page-marker shell. ToolBook has not opened one of these yet. Replacing text inside a book it already opens is `splice_text`, and that leaves the store alone.

## 1.0.5r34

- A click on a field runs the group's buttonClick when the field does not have one. The field's own script stays the mouse handlers.

## 1.0.5r33

- A shape keeps the layer it was stored on. Background objects are `background`. Page objects are `page`.

## 1.0.5r32

- A click on P0 or P1 reaches `send next`. Choosing the page in the list no longer puts it back.
- Begin, the choices, OK, Skip and Back run the quiz script. The Correct box stays hidden, so it does not mark the answer.
- Another book is drawn in the page rectangle, which is how ToolBook sizes the viewer. The book is also looked for in the folders next to the course, not only in core/.

## 1.0.5r31

- P450 draws the background bitmap that is stored in the book.
- Menu runs gotoMenuPage. With the default lesson mode, that is P900.
- Final Quiz runs gotoQuizPage. That is P10004 in this book, or P10003 when the lesson mode is the pretest. It does not open another file.
- A book name matches even when the file on disk is a different case, such as NC81BANK.SBK.

## 1.0.5r30

- The page is not drawn until it fits the window. The raw-size flash on load is gone.
- A click on P0 or P1 runs the background script, which sends next.
- The menu pictures on P900 use the group's jump: P1001, p2001, and the quiz call.
- A quiz choice is the field the book stored. It is not labeled correct or incorrect, and the window does not say which it was.
- A jump to nida81 uses the book beside the course, or one folder up, before the stub in core/.

## 1.0.5r29

- README starts with the from-scratch terminal block: clone or pull `main`, activate `.venv`, install, and open.

## 1.0.5r28

- The equipment bar on P300 is drawn on the frame, not under it. A run of spaces in the copyright is one space.

## 1.0.5r27

- The field font is read. A Wingdings `w` is drawn as a bullet. The words stay in Arial.

## 1.0.5r26

- A jump to another book leaves the first one open. The shell's return, `go to page (nextpage) of book(lastbook)`, comes back to it.
- A blank line at the end of a label no longer pushes the words out of the button.

## 1.0.5r25

- Next, Back, and the other picture buttons take a click. Their script runs. `go to page("P1150")` is the same jump as `go to page "P1150"`.

## 1.0.5r24

- The window has one scale and one offset, and both are applied to every bound before anything is drawn. A picture now grows and shrinks with the text. Tk's canvas scale was moving the picture and leaving its pixels behind.

## 1.0.5r23

- A transparent button's grey matte stays clear. Tk was painting those pixels black, which covered the title, the copyright, and the menu frame.

## 1.0.5r22

- Button pictures need Pillow. Without it the menu frame, the cyan buttons, and the text-panel picture were drawn as white rectangles. The bytes were already in the book.

## 1.0.5r21

- The corner field named Page# shows the page that is open. The saved text was the last page that wrote it: P1270 on the Text background, P1291 on the Overlay background, P100 on the menu background.

## 1.0.5r20

- `go to page` keeps the window that is already up. A background with a fill replaces it. A background without one leaves it, and direct objects stay only on the page now showing. Opening P420 by itself does not invent the chips from P400. An arc is the unfilled curve between its endpoints. The analysis package is v1.0.0r19.

## 1.0.5r19

- An arc is the long sweep of its two rays, filled with the record colour. The fan-out marks on P1150 are no longer boxes. The analysis package is v1.0.0r18.

## 1.0.5r18

- A page with no background fill leaves the previous page where it does not paint. P420 keeps the chips from P410.

## 1.0.5r17

- A page header keeps the coloured bar and drops the grey matte around it. The analysis package is v1.0.0r17.

## 1.0.5r16

- A field with a border is drawn as that frame, and the words are kept inside it. A transparent field still has no box. The analysis package is v1.0.0r16.

## 1.0.5r15

- A button picture is drawn at the button's size. The up face is used unless the button is disabled, pressed, or a checked check box or radio button.
- The four bitmaps that lived in the file table are included. The analysis package is v1.0.0r15.

## 1.0.5r14

- A label stays on one line. The box no longer breaks 7400, INTRODUCTION, or Digital Circuit in the middle of a word. A wide field of near-white text is drawn dark so it shows on the white panel.

## 1.0.5r13

- A `.tbk` with an object store is read from that store. Pages follow the book's page list. A field's text is word 1 of the block at `+0x24`. A class `0x10` outline is mapped onto its bounds. The background fill is the colour at `+0x5B`. A button picture is the bitmap one less than the stored id.

## 1.0.5r12

- The page is scaled to the window after the canvas has a size, and centered. A resize during the first paint is not dropped, so a page no longer stays at its raw size in the corner.

## 1.0.5r11

- A page that already has Back or Next is not given a second copy. The corner stub that repeats one is not drawn. The page is fitted again once the window has a size.
- The analysis package is v1.0.0r12.

## 1.0.5r10

- The analysis package is v1.0.0r11, the one that finds the book script.

## 1.0.5r9

- A `.tbk` or `.sbk` is scanned for compressed handlers, not only the plain words `to handle`. Handlers outside a page are the book script.

## 1.0.5r8

- `--fbk` is not a reader command. FoolbookEditor writes the `.fbk` and the `.fsk`.
- `--freshstart` works again. The converter had taken its place.

## 1.0.5r7

- `python3 -m foolbook --fbk book.tbk` writes `book.fbk` beside the source. An `.sbk` writes an `.fsk`. A folder of books is converted in one run. A TBKX is written the same way.
- The file is what the reader loaded. A button bitmap is still not in a `.tbk` record, so that picture is not in the `.fbk`.

## 1.0.5r6

- A script's `to get` and `to set` blocks are handlers, not just `to handle`. The NIDA system books are written that way.
- A button picture is loaded from beside the book when the path is not already a file.

## 1.0.5r5

- `cryptography` is installed with Foolbook. Opening a book reads the student file, and that import was missing from the package.

## 1.0.5r4

- A system-book page is kept when its name is not `P…`. `tb80hyp` keeps `URL Stuff` and `ChooseFromTextLinesDlg`. An unnamed page is `Page0`.
- `enterBook` runs once when a book opens. A handler closed with `end`, including an `if` that uses the same word, runs through.
- A request for `tb80r.sbk`, `tb80anm.sbk`, or `tb80hyp.sbk` opens the `.fsk` in `core/` first. Those three files were built from the TBKX exports. The raw `.sbk` is the fallback.
- Depends on `openscript_analysis` `v1.0.0r10`.

## 1.0.5r3

- The page is fitted inside the window. A drawing that did not start at the corner was shifted off the top and the left. The window itself opens within the screen.
- A class `0x10` record is no longer also drawn as a rectangle. The pin keeps the outline from its vertices.

## 1.0.5r2

- A class `0x10` irregular polygon is read from its own record. The count is at body `+0x30` and the vertices are at body `+0x38`. The outline is mapped onto the bounds at body `+0x0F`, which moves a shared pin outline and scales a house outline. The fill is the RGB at body `+0x1B`. The `14 00 00` scan is no longer how a polygon is found. A pattern other than `0xFE` is still drawn as that solid color.

## 1.0.5r1

- A page mark is `80 65` or `81 65`, then `00 05 00 02 02`. `81 65` is a nested page. In `9e954d01.tbk`, P440 and P2920 are their own pages instead of staying inside the page before them.

## 1.0.5

- A polygon outline is drawn at its page position, not at the outline's own coordinates. Point lists that fall outside the lesson page are not drawn. P430 no longer fills the window with stacked yellow shapes.
- A Next or Back button moves along the page list when its script does not.

## 1.0.4

- Script expansion depends on `openscript_analysis` `v1.0.0r9`. That release reads the keyword count from byte 0, indexes keywords by id, copies a back-reference from the input, and treats `0xFF` as a new character plus a count.
- The viewer's own `.tbk` decoder stops on a `0x00` literal, matching that release. It still does not follow a back-reference that lands on another back-reference.

## 1.0.3

- A book is read to the end, and the edits in it are applied, before the window opens. A later copy of a page replaces the earlier one.
- One page is one surface. Text, graphics, and buttons use the bounds the book stored. There is no separate text pane and no invented Back/Next bar.
- A `.tbk` widget keeps the twip bounds in its record. The name, the field text, and a button script between that widget and the next one stay with it.
- Next and Back follow that script, or move along the settled page list. A quiz click is checked against the page's Answer property.
- A TBX follows `Book.Pages`. Background objects sit under the page's objects. A button keeps the caption or the bitmap the book named.
- The polygon and rectangle placement from 1.0.2 is still how a `.tbk` drawing is placed. Twip `0, 0` is the window origin.

## 1.0.2

- A polygon record becomes the point array `Polygon` is given. Each twip is `(coord * dpi + 720) / 1440`.
- Rectangle, ellipse, round rect, polyline, and arc use the same conversion. `Pie` is not called. A bracket does not invent its points.
- Each object is placed from its twip bounds. Twip `0, 0` is the window origin.
- A `.tbk` page now carries those shapes into the viewer.
- NearScript heap, value stack, resource session, book API, and object layer.
- One module file each for `bas`, `rtm`, `utl`, `rcr`, `w16`, `w32`, and `w64`.

## 1.0.1r2

- Content rectangle extraction. Bounds at -16, fill at -4, marker `01 00 00 04`.

## 1.0.1

- Rudimentary graphics in the GUI viewer: explicit polygons and bounds-only rectangles from the page blob.
- System-book contract: core `.fsk` load first, user `.fsk` load after as mods.
- `projectphilosophy.md` added.

## 1.0.0

First release.
