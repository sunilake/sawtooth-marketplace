/**
 * Copyright 2017 Intel Corporation
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
 * ----------------------------------------------------------------------------
 */
'use strict'

const m = require('mithril')
const _ = require('lodash')
const octicons = require('octicons')

/**
 * Returns a header styled to be a page title
 */
const title = title => m('h2.text-center.mb-3', title)

/**
 * Returns a sub-header styled to contain a short description
 */
const description = desc => m('h4.text-center.text-muted.mb-3', desc)

/**
 * Returns a row of any number of columns, suitable for placing in a container
 */
const row = columns => {
  if (!_.isArray(columns)) columns = [columns]
  return m('.row', columns.map(col => m('.col-md', col)))
}

/**
 * Divides columns into a series of rows with a number of columns per row
 */
const sectionedRows = (columns, count = 2) => {
  return columns
    .reduce((pairs, col) => {
      if (_.last(pairs).length < 2) _.last(pairs).push(col)
      if (_.last(pairs).length === 2) pairs.push([])
      return pairs
    }, [[]])
    .map(pair => {
      if (pair.length === 0) return null
      return row(pair)
    })
}

/**
 * Returns a sub-header followed by related info
 */
const labeledField = (label, info) => {
  return m('.labeled-field.mt-5', [
    m('h5', label),
    info
  ])
}

/**
 * Returns a mithriled icon from Github's octicon set
 */
const icon = name => m.trust(octicons[name].toSVG())

module.exports = {
  title,
  description,
  row,
  sectionedRows,
  labeledField,
  icon
}
