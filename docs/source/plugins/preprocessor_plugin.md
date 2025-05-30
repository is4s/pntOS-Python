# Preprocessor Plugin

A {py:obj}`Preprocessor Plugin<pntos.api.PreprocessorPlugin>` allows for data
manipulation before incoming {py:obj}`Message<pntos.api.Message>`s are passed into the
filter. It takes in one message, and then returns 0, 1, or multiple messages. Imaging a
simple preprocessor which validates incoming {term}`ASPN` messages before they enter the
filter. It might return 0 messages if it encounters a faulty message, and return 1
message (pass through the input message) if the message is valid. A
{py:obj}`Preprocessor Plugin<pntos.api.PreprocessorPlugin>` might also be used for
something like a camera where a frame message comes in, and then range to point messages
come out for each observation in the frame. In this case, 1 message would come into the
plugin, and more than 1 message may come out of the plugin.

<!-- TODO (#178) https://git.aspn.us/pntos/pntos-python/-/issues/178 -->