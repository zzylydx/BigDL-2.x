/*
 * Copyright 2016 The BigDL Authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.intel.analytics.bigdl.dllib.keras.layers

import com.intel.analytics.bigdl.dllib.nn.abstractnn.AbstractModule
import com.intel.analytics.bigdl.dllib.tensor.Tensor
import com.intel.analytics.bigdl.dllib.utils.Shape
import com.intel.analytics.bigdl.dllib.keras.Sequential
import com.intel.analytics.bigdl.dllib.keras.serializer.ModuleSerializationTest


class GlobalAveragePooling1DSpec extends KerasBaseSpec{

  "GlobalAveragePooling1D" should "be the same as Keras" in {
    val kerasCode =
      """
        |input_tensor = Input(shape=[3, 24])
        |input = np.random.random([2, 3, 24])
        |output_tensor = GlobalAveragePooling1D()(input_tensor)
        |model = Model(input=input_tensor, output=output_tensor)
      """.stripMargin
    val seq = Sequential[Float]()
    val layer = GlobalAveragePooling1D[Float](inputShape = Shape(3, 24))
    seq.add(layer)
    seq.getOutputShape().toSingle().toArray should be (Array(-1, 24))
    checkOutputAndGrad(seq.asInstanceOf[AbstractModule[Tensor[Float], Tensor[Float], Float]],
      kerasCode)
  }

}

class GlobalAveragePooling1DSerialTest extends ModuleSerializationTest {
  override def test(): Unit = {
    val layer = GlobalAveragePooling1D[Float](inputShape = Shape(3, 24))
    layer.build(Shape(2, 3, 24))
    val input = Tensor[Float](2, 3, 24).rand()
    runSerializationTest(layer, input)
  }
}
